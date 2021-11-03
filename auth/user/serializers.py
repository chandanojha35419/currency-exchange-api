import logging

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from rest_framework import serializers, status

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response

from labs import service
from labs.exceptions import ValidationError, AuthenticationError, Forbidden, Reason, success_response, ServerError
from labs.fields import validate_email
from labs.generics import ReadOnlyModelSerializer
from labs.model_serializer import ModelSerializer
from labs.modelfield import PhoneNumber
from labs.utils import get_client_token, split_fullname
from . import get_int_config
from .authentication import find_user
from .models import OTP, Token, create_user
from .texts import get_app_text as _t

logger = logging.getLogger(__name__)


class OtpContext:
	PWD_RESET = 'PR'
	VERIFY_EMAIL = 'PVE'
	VERIFY_MOBILE = 'PVM'
	OTP_LOGIN = 'OL'


class MaxFieldLen:
	USERNAME = EMAIL = 254
	MOBILE = 12
	PASSWORD = 40
	FULL_NAME = 100


def serializer_username_field(**kwargs):
	return serializers.CharField(max_length=MaxFieldLen.USERNAME, **kwargs)


def serializer_email_field(**kwargs):
	if 'required' not in kwargs:
		kwargs['required'] = False
	return serializers.CharField(min_length=8, max_length=MaxFieldLen.EMAIL, validators=[validate_email], **kwargs)


def serializer_password_field(**kwargs):
	return serializers.CharField(min_length=8, max_length=MaxFieldLen.PASSWORD, style={'input_type': 'password'},
								 **kwargs)


def serializer_name_field(**kwargs):
	if 'required' not in kwargs:
		kwargs['required'] = False
	return serializers.CharField(allow_blank=True, max_length=MaxFieldLen.FULL_NAME, **kwargs)


class ValidateUserMixin:
	
	def validate(self, attrs):
		assert attrs.get('username') or attrs.get('email') or attrs.get('mobile')
		
		user = find_user(**attrs)
		if not user:
			raise ValidationError(_t('invalid_username'))
		
		attrs['user'] = user
		attrs.update(super().validate(attrs))
		return attrs


class LoginSerializer(ValidateUserMixin, serializers.Serializer):

	username = serializer_username_field()
	password = serializers.CharField(max_length=MaxFieldLen.PASSWORD)

	@classmethod
	def get_token_class(cls):
		return Token

	def is_login_allowed(self, user):
		return True

	def validate(self, attrs):
		"""
		Over-rides the response message of Username mixin where user is not found
		Returns the general unable-to-login message for both user-name and password fail
		"""
		try:
			return super().validate(attrs)
		except ValidationError as e:
			raise AuthenticationError(_t('unable_to_login'))

	def create(self, validated_data):
		request = self.context['request']
		user = authenticate(request, **validated_data)

		if not user:
			raise AuthenticationError(_t('unable_to_login'))

		if not self.is_login_allowed(user):
			raise Forbidden(_t('login_not_allowed'), reason=Reason.Http403.ACCESS_DENIED)

		if not user.is_active:
			raise Forbidden(_t('account_disabled'), reason=Reason.DISABLED)

		token = self.get_token_class().create_token(client_token=get_client_token(request), user=user)
		return Response({'token': token.key, 'expiry': token.expiry}, status=status.HTTP_200_OK)


class OTPRequestSerializer(serializers.Serializer):
	otp_context = None  # Should be set by child class.
	event_name = None  # Should be set by child class.
	success_response = "OTP sent successfully"
	
	username = serializers.CharField(max_length=MaxFieldLen.USERNAME)
	
	def validate(self, attrs):
		attrs = super().validate(attrs)
		username = attrs.pop('username')
		try:
			validate_email(username)
			attrs['email'] = username
		except DjangoValidationError:
			attrs['mobile'] = PhoneNumber.parse(username)
		return attrs
	
	def send_otp(self, mobile, email, **kwargs):
		otp_code = OTP.get_shared_otp_code(mobile, email, self.otp_context)
		service.send_otp_mail(mobile, email, self.event_name, otp_code)
	
	def create(self, validated_data):
		self.send_otp(validated_data.get('mobile'), validated_data.get('email'))
		return success_response(self.success_response, code=status.HTTP_201_CREATED)


class OTPConfirmSerializer(serializers.Serializer):
	otp_context = None  # Should be set by child class.
	
	username = serializers.CharField(max_length=MaxFieldLen.USERNAME)
	otp = serializers.CharField(min_length=4, max_length=12)
	
	def validate(self, attrs):
		attrs = super().validate(attrs)
		
		otp = attrs['otp']
		attrs['otp'] = OTP.check_otp(otp, attrs.get('username'), self.otp_context)
		return attrs


class PasswordResetMixin(ValidateUserMixin):
	
	def validate(self, attrs):
		attrs = super().validate(attrs)
		return attrs


class PasswordResetRequestSerializer(PasswordResetMixin, OTPRequestSerializer):
	otp_context = OtpContext.PWD_RESET
	event_name = 'password_reset_otp'
	success_response = _t('pwd_reset_otp')


class PasswordResetConfirmSerializer(PasswordResetMixin, OTPConfirmSerializer):
	"""
	Serializer for handling password reset confirmation using OTP.
	"""
	otp_context = OtpContext.PWD_RESET
	password = serializer_password_field()
	
	def create(self, validated_data):
		# OTP has already been validated
		
		user = validated_data['user']
		with transaction.atomic():
			# set the new password and delete the otp
			user.set_password(validated_data['password'])
			user.save()
			
			user.token_set.all().delete()
			
			validated_data['otp'].delete()
		return success_response(_t('password_changed'), code=status.HTTP_202_ACCEPTED)


class LoginOTPRequestSerializer(OTPRequestSerializer):
	otp_context = OtpContext.OTP_LOGIN
	event_name = 'login_otp'


class LoginOTPConfirmSerializer(ValidateUserMixin, OTPConfirmSerializer):
	otp_context = OtpContext.OTP_LOGIN
	
	@classmethod
	def get_token_class(cls):
		return Token
	
	def is_login_allowed(self, user):
		return True
	
	def create(self, validated_data):
		# Auto signup, return token
		user = validated_data['user']
		
		if not self.is_login_allowed(user):
			raise Forbidden(_t('login_not_allowed'), reason=Reason.Http403.ACCESS_DENIED)
		
		if not user.is_active:
			raise Forbidden(_t('account_disabled'), reason=Reason.DISABLED)
		
		token = self.get_token_class().create_token(user=user, client_token=get_client_token(request=self.context['request']))
		validated_data['otp'].delete()
		return Response(data={'token': token.key}, status=status.HTTP_201_CREATED)


class PasswordChangeSerializer(serializers.Serializer):
	"""
	Serializer for changing password of an already authenticate user.
	"""
	old_password = serializers.CharField(max_length=MaxFieldLen.PASSWORD)
	password = serializer_password_field()
	
	def get_user(self):
		return self.context['request'].user
	
	def validate_old_password(self, value):
		# Check if provided current password is correct
		user = self.get_user()
		if not user.check_password(value):
			raise AuthenticationError(message=_t('incorrect_current_password'))
		return value
	
	def create(self, validated_data):
		user = self.get_user()
		with transaction.atomic():
			user.set_password(validated_data['password'])
			user.save()
			
			user.token_set.all().delete()  # deleting existing tokens to force re-login
		
		return success_response(_t('password_changed'), code=status.HTTP_202_ACCEPTED)


class SignupSerializer(serializers.Serializer):
	"""
	Serializer for signing up a new user
	"""
	email = serializer_email_field(required=True)
	name = serializer_name_field()
	password = serializer_password_field()
	
	def validate_email(self, value):
		if get_user_model().objects.filter(email=value).exists():
			raise ValidationError(_t('user_exists_email_{0}', value))
		return value
	
	def create(self, validated_data):
		try:
			return create_user(is_staff=False, **validated_data)
		except Exception as e:
			msg = _t('registration_error')
			logger.exception(e, msg)
			raise ServerError(message=msg, detail=e)


# << =============
# UserSerializers
#

class MyUserSerializer(ModelSerializer):
	"""
	Serializer for updating/retrieving logged-in user object (excluding sensitive fields)
	"""
	name = serializer_name_field()
	
	class Meta:
		model = get_user_model()
		fields = ('email', 'name', 'last_login')
		read_only_fields = ('last_login',)
	
	def validate_email(self, value):
		if get_user_model().objects.filter(email=value).exists():
			raise ValidationError(_t('user_exists_email_{0}', value))
		return value
	
	def validate(self, attrs):
		name = attrs.pop('name', None)
		if name:
			attrs['first_name'], attrs['last_name'] = split_fullname(name)
		return attrs


class MyStaffSerializer(MyUserSerializer):
	"""
	Serializer for updating/retrieving staff-user object (excluding sensitive fields)
	Allows Staff-User Update, provides validation, basic defaults required for Staff-UserUpdate
	Provides StaffUser Response-structure
	"""
	
	class Meta:
		model = get_user_model()
		fields = ('email', 'name', 'is_superuser', 'is_staff', 'last_login')
		read_only_fields = ('is_superuser', 'is_staff', 'last_login',)


class UserSerializer(ModelSerializer):
	# name = serializers.CharField()
	
	class Meta:
		model = get_user_model()
		exclude = ('username', 'password', 'first_name', 'user_permissions', 'groups', 'last_name')
		read_only_fields = ('is_superuser', 'is_staff', 'last_login', 'date_joined', 'email')
	
	def validate(self, attrs):
		name = attrs.pop('name', None)
		if name:
			attrs['first_name'], attrs['last_name'] = split_fullname(name)
		return attrs


class StaffSerializer(ReadOnlyModelSerializer):
	"""
	Minimal staff fields to be sent to client
	"""
	name = serializers.CharField()
	
	class Meta:
		model = get_user_model()
		fields = ('id', 'name', 'email', 'is_active')
		read_only_fields = ('name', 'email', 'is_active')


class UserCreateSerializer(SignupSerializer):
	"""
	Allows User Creation, provides validation, basic defaults required for UserCreation
	"""
	is_staff = serializers.BooleanField(default=False)
	
	def validate_staff(self, value):
		user = self.request.user
		if not user or not user.is_staff:
			raise Forbidden(detail=_t('user_must_be_staff'))
		
		if value and not user.is_superuser:
			raise Forbidden(_t('admin_only'), detail=_t('Only admin can create new staff'))
		
		return value
	
	def create(self, validated_data):
		try:
			return create_user(**validated_data)
		except Exception as e:
			msg = _t('registration_error')
			logger.exception(e, msg)
			raise ServerError(message=msg, detail=e)


class AdminPasswordResetSerializer(ModelSerializer):
	password = serializer_password_field(required=False)
	
	class Meta:
		model = get_user_model()
		fields = ('password',)
	
	def validate(self, data):
		user = self.instance
		if user.is_superuser:
			if user != self.request.user:
				raise Forbidden(message=_t('superuser_password_reset_forbidden'))
		
		if not data.get('password'):
			data['password'] = get_int_config('user.staff_default_password')
		
		return data
	
	def update(self, instance, validated_data):
		instance.set_password(validated_data['password'])
		instance.save()
		return success_response('password-reset successful')

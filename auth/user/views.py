import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from labs import utils
from labs.exceptions import success_response, ValidationError
from labs.utils import get_client_token
from labs.views import RetrieveUpdateAPIView, CreateAPIView, IdListAPIView, ListCreateAPIView, UpdateAPIView
from .models import Token
from .permissions import AuthenticatedViewMixin, IsAdmin
from .serializers import (
	LoginSerializer, SignupSerializer,
	PasswordResetRequestSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer,
	MyUserSerializer, MyStaffSerializer, UserSerializer, UserCreateSerializer,
	AdminPasswordResetSerializer,
	LoginOTPRequestSerializer, LoginOTPConfirmSerializer)
from .texts import get_app_text as _t


logger = logging.getLogger(__name__)


class LoginView(CreateAPIView):
	"""
	Handles user login, returns access token on success. Updates users last login time.
	"""
	serializer_class = LoginSerializer


class LoginOTPRequestView(CreateAPIView):
	serializer_class = LoginOTPRequestSerializer


class LoginOTPConfirmView(CreateAPIView):
	serializer_class = LoginOTPConfirmSerializer


class BaseLogoutViewMixin:
	def post(self, request, *args, **kwargs):
		"""
		Logs out the currently authenticated user identified by the auth-token in header, from current or all devices
		---
		parameters:
			- name: logout_all
			  description: set it to true if user wants to log out from all logged in devices.
			  type: string
			  paramType: query
		"""
		try:
			# check query param for 'logout from all' option
			if utils.as_bool(request.query_params.get('logout_all')):
				self.get_user(request).token_set.all().delete()
				return success_response(_t('all_devices_logout'))

			# delete current token
			request.auth.delete()

		except (APIException, Token.DoesNotExist) as e:
			logger.warning(e)
			return ValidationError(detail=e.detail)

		return success_response(_t('logout'))


class LogoutView(AuthenticatedViewMixin, BaseLogoutViewMixin, views.APIView):
	pass


class PasswordResetRequestView(CreateAPIView):
	"""
	Handles password reset request for the given username. Sends OTP to register email or phone
	"""
	serializer_class = PasswordResetRequestSerializer

	def perform_create(self, serializer):
		super().perform_create(serializer)
		first_time_login = serializer.validated_data['user'].last_login is None
		return Response(data={"first_time_login": first_time_login, 'message': serializer.success_response})


class PasswordResetConfirmView(CreateAPIView):
	"""
	Handles password reset for given username using the OTP sent to registered email/phone earlier
	"""
	serializer_class = PasswordResetConfirmSerializer


class PasswordChangeView(AuthenticatedViewMixin, CreateAPIView):
	"""
	Handles password change for currently authenticated user.
	Needs 'old password' and the new 'password'
	"""
	serializer_class = PasswordChangeSerializer


class SignupView(CreateAPIView):
	"""
	Signs up a new user, Needs valid (unique)username and password
	Logs in the user on successful registration and returns the corresponding access_token
	"""
	serializer_class = SignupSerializer

	def perform_create(self, serializer):
		# First save the user
		with transaction.atomic():
			user = super().perform_create(serializer)
		token = Token.objects.create(user=user, client_token=get_client_token(self.request))
		return Response(data={'token': token.key}, status=status.HTTP_201_CREATED)


class MyUserView(AuthenticatedViewMixin, RetrieveUpdateAPIView):
	"""
	Handles User profile retrieval(GET) or update(PATCH) for currently authenticated user.
	Only relevant fields are exposed for reading or writing (see serializer)
	"""
	serializer_class = MyUserSerializer
	model_class = get_user_model()

	def get_object(self):
		return self.request.user

	def get_serializer_class(self):
		# different serializer for Staff and it will have access to more fields
		return MyStaffSerializer if self.request.user.is_staff else super().get_serializer_class()


# ============================
# Admin views
#
class UserListViewMixin(AuthenticatedViewMixin):
	permission_classes = (IsAdmin,)
	model_class = get_user_model()
	ordering = ('-id',)


class UserIdListView(UserListViewMixin, IdListAPIView):
	pass


class UserListView(UserListViewMixin, ListCreateAPIView):
	""" Admin only - List/Create users"""
	model_class = get_user_model()
	serializer_class = UserSerializer

	def get_serializer_class(self):
		return UserCreateSerializer if self.request.method == 'POST' else super().get_serializer_class()

	def get_response_serializer_class(self):
		return UserSerializer


class UserView(AuthenticatedViewMixin, UpdateAPIView):
	""" Admin only - Get/Update user detail """
	permission_classes = (IsAdmin,)

	model_class = get_user_model()
	serializer_class = UserSerializer


class AdminPasswordResetView(AuthenticatedViewMixin, UpdateAPIView):
	""" Admin only - Allows a super-user to force-reset any other non-admin user's password """
	permission_classes = (IsAdmin,)

	model_class = get_user_model()
	serializer_class = AdminPasswordResetSerializer

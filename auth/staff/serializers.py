from django.contrib.auth import get_user_model
from rest_framework import serializers

from labs.exceptions import ValidationError, Forbidden
from labs.generics import ReadOnlyModelSerializer
from labs.model_serializer import ModelSerializer
from labs.utils import split_fullname
from . import bot_staff
from .models import Staff, create_staff
from .texts import get_app_text as _t
from ..user.serializers import MyStaffSerializer as BaseStaffSerializer, UserSerializer, serializer_email_field, \
	serializer_name_field, serializer_password_field


def check_active_staff(staff):
	if not (isinstance(staff, Staff) and staff.user.is_staff):
		raise ValidationError(_t('user_must_be_staff'))

	if not staff.user.is_active:
		raise ValidationError(_t('staff_not_active'))

	if staff == bot_staff():
		raise ValidationError(_t('cannot_assign_bot'))


class MyStaffSerializer(ModelSerializer):
	email = serializer_email_field(source='user.email', read_only=True, default=None)
	name = serializer_name_field()
	user = BaseStaffSerializer(read_only=True)

	class Meta:
		model = Staff
		read_only_fields = ('emp_id', )

	def update(self, instance, validated_data):
		name = validated_data.pop('name', None)
		if name:
			instance.user.first_name, instance.user.last_name = split_fullname(name)
			instance.user.save()

		return super().update(instance, validated_data)


class StaffLookupSerializer(ReadOnlyModelSerializer):
	"""
	Minimal staff fields to be sent to client
	"""
	name = serializer_name_field(read_only=True)
	email = serializer_email_field(source='user.email', read_only=True, default=None)
	is_active = serializers.BooleanField(source='user.is_active', read_only=True, default=False)
	is_bot = serializers.BooleanField(read_only=True)

	class Meta:
		model = Staff
		fields = ('id', 'name', 'mobile', 'email', 'is_active', 'is_bot')
		

class StaffSerializer(MyStaffSerializer):
	email = serializer_email_field(source='user.email', required=True)
	password = serializer_password_field(write_only=True)

	user = UserSerializer(read_only=True)

	class Meta:
		model = Staff
		fields = '__all__'
		read_only_fields = ('emp_id',)

	def validate_email(self, value):
		if not value.endswith('@classicinformatics.com'):
			raise ValidationError(_t('invalid_staff_email'))

		if get_user_model().objects.filter(email=value).exists():
			raise ValidationError(_t('user_exists_email_{0}', value))

		return value

	def create(self, validated_data):
		user_data = validated_data.pop('user')
		password = validated_data.pop('password')
		name = validated_data.pop('name', '')
		return create_staff(email=user_data['email'], password=password, name=name, **validated_data)

	def update(self, instance, validated_data):
		if instance.user.is_superuser:
			raise Forbidden('Cannot modify an admin')

		user_data = validated_data.pop('user', None)
		if user_data and 'email' in user_data:
			instance.user.email = user_data['email']
			instance.user.save()

		return super().update(instance, validated_data)

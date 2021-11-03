from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _t
from labs.phonenumber import PhoneNumber

__author__ = 'chandanojha'


class PhoneNumberDescriptor:
	"""
	The descriptor for the phone number attribute on the model instance.
	Returns a PhoneNumber when accessed so you can do stuff like::
	   instance.phone_number = PhoneNumber('+91-9876543210')
	   instance.phone_number = '+91-9876543210'
	   instance.phone_number.e164
	"""
	
	def __init__(self, field):
		self.field = field
	
	def __set__(self, instance, value):
		instance.__dict__[self.field.name] = PhoneNumber.parse(value)


class PhoneNumberField(models.CharField):
	descriptor_class = PhoneNumberDescriptor
	default_validators = [MinLengthValidator(8)]
	# default_validators = [MinLengthValidator(8), PhoneNumber.validator()]
	
	description = _t("Phone number model field, wraps 'PhoneNumber' data class")
	
	def __init__(self, *args, **kwargs):
		kwargs.setdefault("max_length", 16)
		super().__init__(*args, **kwargs)
	
	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		
		# Remove the default values
		if kwargs.get("max_length") == 16:
			del kwargs["max_length"]
		
		return name, path, args, kwargs
	
	def from_db_value(self, value, expression, connection):
		return PhoneNumber.parse(value)
	
	def to_python(self, value):
		return PhoneNumber.parse(value)

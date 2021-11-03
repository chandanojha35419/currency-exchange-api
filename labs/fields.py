import re

from django.core.validators import RegexValidator, EmailValidator, MinValueValidator
from django.db import models
from django.utils.deconstruct import deconstructible
from rest_framework import status


__author__ = 'chandanojha'

from labs import fieldlen
from labs.exceptions import ValidationError
from labs.phonenumber import PhoneNumber
from django.utils.translation import ugettext_lazy as _t

validate_email = EmailValidator(_t('invalid_email'), status.HTTP_400_BAD_REQUEST)
validate_mobile = PhoneNumber.validator()
validate_zip = RegexValidator(re.compile(r'^[1-9][0-9]{5}$'), _t("Invalid pin code."), status.HTTP_400_BAD_REQUEST)


# Quick field factory methods to keep the field length consistent across app
#
def default_char_field(max_length=255, **kwargs):
	# if null=True and blank is not specified then assume it to be True as well
	if kwargs.get('null'):
		kwargs.setdefault('blank', True)
	return models.CharField(max_length=max_length, **kwargs)


def short_code_field(max_length=fieldlen.SHORT_CODE, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


def long_code_field(max_length=fieldlen.LONG_CODE, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


def tiny_char_field(max_length=fieldlen.TINY_CHAR, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


def short_char_field(max_length=fieldlen.SHORT_CHAR, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


def short_medium_char_field(max_length=fieldlen.SHORT_MEDIUM_CHAR, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


def medium_char_field(max_length=fieldlen.MEDIUM_CHAR, **kwargs):
	return default_char_field(max_length=max_length, **kwargs)


@deconstructible
class KeyFieldValidator:
	"""
		All lower-case 'dotted' (configurable) string where each word can be further '_' separated alphanum.

		First word must start with alpha and should be of min. 2 chars.

		Valid Examples:
			this.that
			this.this_or_that.that
			my_app.config_value

		Invalid:
			a.something         (first word > 2 chars)
			2a.b.c              (first word starts with number)
			_abcd.somethis__    (Word should start/end with alphanum)
	"""
	def __init__(self, sep='.'):
		self.sep = sep

	def __call__(self, value):
		if not value.islower:
			raise ValidationError("Only lower case alphabets allowed")

		for i, word in enumerate(value.split(self.sep)):
			if i == 0 and (len(word) < 2 or not word[0:1].isalpha()):
				raise ValidationError("First word '{0}' should start with alpha and of minimum 2 chars".format(word))

			# Allow '_' but not at the start or a word
			for w in word.split('_'):
				if not w.isalnum():
					raise ValidationError("Invalid word: '{0}', should be alpha-numeric"
					                      " optionally separated by '_'".format(word))


def key_char_field(sep='.', max_length=fieldlen.SHORT_MEDIUM_CHAR, unique=True, **kwargs):
	v = KeyFieldValidator() if sep == '.' else KeyFieldValidator(sep)   # no need to pass default
	kwargs.setdefault('validators', [v])
	return default_char_field(max_length=max_length, unique=unique, **kwargs)


def default_null_char_field(**kwargs):
	return NullCharField(null=True, blank=True, **kwargs)


def default_text_field(null=True, **kwargs):
	# if null=True and blank is not specified then assume it to be True as well
	if null:
		kwargs.setdefault('blank', True)
	return models.TextField(null=null, **kwargs)


def default_url_field(**kwargs):
	# if null=True and blank is not specified then assume it to be True as well
	if kwargs.get('null'):
		kwargs.setdefault('blank', True)
	return models.URLField(**kwargs)


def default_currency_field(allow_negative=False, **kwargs):
	if not allow_negative:
		if 'validators' in kwargs:
			kwargs['validators'].append(MinValueValidator(0))
		else:
			kwargs['validators'] = [MinValueValidator(0)]
	return models.FloatField(**kwargs)


def default_size_field(null=True, **kwargs):
	if 'validators' not in kwargs:
		kwargs['validators'] = [MinValueValidator(0)]
	else:
		kwargs['validators'].append(MinValueValidator(0))

	if 'help_text' not in kwargs:
		kwargs['help_text'] = "In inch, max 1 decimal digit"
	return models.FloatField(null=null, **kwargs)


def auto_time_field(update=False, **kwargs):
	"""
	Time-stamp fields
	:param update: True => auto_now, False => auto_now_add
	:param kwargs:
	:return:
	"""
	return DateTimeField(auto_now=True, **kwargs) if update else models.DateTimeField(auto_now_add=True, **kwargs)


def default_fk_field(model_class, on_delete=models.PROTECT, **kwargs):
	return models.ForeignKey(model_class, on_delete=on_delete, **kwargs)


def default_one_to_one_field(model_class, on_delete=models.PROTECT, **kwargs):
	return models.OneToOneField(model_class, on_delete=on_delete, **kwargs)


# ----------------------------
# Custom fields subclasses
#

class NullCharField(models.CharField):
	"""
	A field of type CharField that allows empty strings to be stored as NULL.
	"""
	description = "CharField that stores NULL but returns ''."

	def from_db_value(self, value, expression, connection):
		"""
		gets the value from the db and changes it to '' if it is 'None'.
		"""
		if value is None:
			return ''

		return value

	def to_python(self, value):
		"""
		gets value from db or an instance and changes it to '' if it is 'None'.
		"""
		if isinstance(value, models.CharField):
			# if an instance, just return the instance.
			return value
		if value is None:
			# if value in db is null, convert it to ''.
			return ''

		# otherwise just return the value.
		return value

	def get_prep_value(self, value):
		"""
		catches value just before sending to db.
		"""
		if value is '':
			# convert the empty string to NULL before sending to db.
			return None

		# otherwise, just pass the value.
		return value


class DateTimeField(models.DateTimeField):
	"""
	To be used as auto-updated datetime field

	Same as Django's DateTimeField but in case of auto_now:
	 - doesn't set the field at time of creation and
	 - assumes the field to be nullable if not explicitly set
	"""

	def __init__(self, **kwargs):
		if kwargs.get('auto_now') and 'null' not in kwargs:
			# Assume null=True if not explicitly set
			kwargs['null'] = True

		super().__init__(**kwargs)

	def pre_save(self, model_instance, add):
		# Bypass base class as it would update the field even at creation or when 'skip_auto_now' is set.
		if hasattr(model_instance, 'skip_auto_now') or (self.auto_now and add):
			return getattr(model_instance, self.attname)
		return super().pre_save(model_instance, add)

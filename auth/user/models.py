import binascii
import logging
import os
import random
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import user_logged_in
from django.contrib.auth.models import AbstractUser
from django.db import models, IntegrityError, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from labs import fields
from labs.exceptions import ServerError, ValidationError, Reason, NotFound
from labs.models import BlankModel
from labs.utils import split_fullname
from . import get_int_config, get_config
from .texts import get_app_text as _t

__author__ = 'chandanojha'

logger = logging.getLogger(__name__)


class CustomUser(AbstractUser):
	"""
	Custom User model, to add/customize fields in django's default user. To use this, add the following in you settings file.
	You can also further subclass this but then you have to update the following line to use your class.

	AUTH_USER_MODEL = 'user.CustomUser'
	"""
	email = models.EmailField(_('email address'), blank=True, null=True, unique=True)

	class Meta:
		db_table = 'auth_user'

	def delete_existing_tokens(self):
		# deletes existing tokens of user or logging out user of all devices
		Token.objects.filter(user=self).delete()

	def save(self, *args, **kwargs):
		# if email is empty string '', convert it to NULL (None)
		if self.email is '':
			self.email = None
		return super().save(*args, **kwargs)

	def get_username(self):
		if self.email:
			return self.email
		if self.mobile:
			return self.mobile
		return self.username

	def get_short_name(self):
		short_name = super().get_short_name()
		if short_name:
			short_name = short_name.split(maxsplit=1)[0]
			return short_name.capitalize()
		elif self.email:
			return self.email[:self.email.index("@")]
		return ''

	@property
	def name(self):
		return self.get_full_name()

	@property
	def get_salutation(self):
		return self.get_short_name()

	def make_active(self, auto_login=False, client_token=''):
		"""
		marks a user as active, sends welcome email and sms and if auto_login is True then creates an auth_token for
		device identified by client_token.
		:param auto_login: Boolean that marks if auto_login is enabled or not
		:param client_token: unique device identifier
		:return: user, token tuple
		"""
		self.is_active = True
		self.save()
		auth_token = None
		if auto_login:
			auth_token = Token.objects.create(user=self, client_token=client_token).key
		return auth_token


def create_user(email, password, name, **kwargs):
	rand_username = get_random_string(length=get_int_config('user.username.length'))
	username = kwargs.pop('username', rand_username)

	first_name, last_name = split_fullname(name)
	return CustomUser.objects.create_user(username=username, email=email, password=password,
	                                     first_name=first_name, last_name=last_name, **kwargs)


class AbstractToken(BlankModel):
	key = fields.default_char_field(max_length=40, primary_key=True)
	client_token = fields.tiny_char_field(null=True)
	created = fields.auto_time_field()
	expiry = models.DateTimeField()

	class Meta:
		abstract = True

	def __str__(self):
		return self.key

	def build(self):
		self.key = AbstractToken.generate_key()
		self._set_expiry(get_int_config('user.token.lifetime'))

	def save(self, *args, **kwargs):
		if not self.key:
			self.build()
		return super().save(*args, **kwargs)

	def refresh(self, save=True):
		self._set_expiry(get_int_config('user.token.lifetime'), save=save)
		return self.key

	def expire(self, save=True):
		self._set_expiry(0, save=save)
		return None

	def _set_expiry(self, life_time, save=False):
		self.expiry = timezone.now() + timedelta(days=life_time)
		if save:
			self.save()

	@staticmethod
	def generate_key():
		return binascii.hexlify(os.urandom(get_int_config('user.token.length'))).decode()

	@classmethod
	def create_token(cls, client_token, user):
		token, created = cls.objects.get_or_create(user=user, client_token=client_token)
		if not created:
			logger.info(_t('reusing_token'))
			if timezone.now() > (token.expiry):
				# Token expired, refresh it..
				token.refresh()

		user_logged_in.send(sender=user.__class__, user=user)
		return token


class Token(AbstractToken):
	user = fields.default_fk_field(settings.AUTH_USER_MODEL)

	class Meta:
		db_table = 'auth_token'
		unique_together = ('user', 'client_token')


class OTP(BlankModel):
	email_or_mobile = fields.default_char_field()
	context = fields.short_code_field()
	otp = fields.long_code_field()
	expires_on = models.DateTimeField()

	class Meta:
		db_table = 'auth_otp'
		unique_together = ('email_or_mobile', 'context',)

	def is_valid(self, for_minutes=0):
		now = timezone.now() + timedelta(minutes=for_minutes)
		return self.expires_on.__gt__(now)

	def save(self, *args, **kwargs):
		try:
			return super().save(*args, **kwargs)
		except IntegrityError:
			raise ServerError(_t('otp_sending_failed'))

	def __str__(self):
		return "[" + super().__str__() + "]: (" + str(self.id) + ", " + self.otp + ")"

	@classmethod
	def check_otp(cls, otp, email_or_mobile, context):
		message = _t('invalid_otp_{0}', otp)
		try:
			otp = cls.objects.get(otp=otp, email_or_mobile=email_or_mobile, context=context)
		except cls.DoesNotExist:
			raise NotFound(message)
		except OTP.MultipleObjectsReturned:
			assert False, "Should not happen!"

		if not otp.is_valid():
			raise ValidationError(message, reason=Reason.EXPIRED)

		return otp

	@classmethod
	def generate_otp(cls, length=None, allowed_chars=string.digits):
		length = length or get_int_config('user.otp.length')
		otp = get_random_string(length=length, allowed_chars=allowed_chars)
		if otp[0] == '0':
			# We don't want our otp to start with '0'
			otp = random.choice('123456789') + otp[1:]
		return otp

	@classmethod
	def get_shared_otp_code(cls, mobile, email, context, lifetime=None, length=None):
		""" Uses the same OTP code for both email and mobile

			Note that since same OTP is used for both email and mobile, you should not use it for verification.
			It is useful for Login, PwdReset etc.

		:return: OTP code (and not the otp object)
		"""
		assert email or mobile, "Either Email or Mobile must be Verified for Otp."

		otp = None
		with transaction.atomic():
			if mobile:
				otp = cls.get_otp(mobile, context, lifetime=lifetime, length=length)

			if email:
				# reuse the OTP code we just sent on mobile (if)
				otp = cls.get_otp(email, context, lifetime=lifetime, length=length, code=otp and otp.otp)
		return otp and otp.otp

	@classmethod
	def get_otp(cls, email_or_mobile, context, lifetime=None, length=None, code=None):
		lifetime = lifetime or get_int_config('user.otp.lifetime')
		with transaction.atomic():
			try:
				otp = cls.objects.get(email_or_mobile=email_or_mobile, context=context)
				if otp.is_valid():
					# OTP exists and is valid. Just resend it.
					return otp
				else:
					# OTP exists and is invalid. Delete the OTP and create a new one while preserving the context_data.
					otp.delete()
			except cls.DoesNotExist:
				# OTP does not exists. A new one will be created.
				pass

			except cls.MultipleObjectsReturned:
				# An Unlikely situation, should never happen. Delete all OTPs of this user and of given context.
				cls.objects.filter(email_or_mobile=email_or_mobile, context=context).delete()

			code = code or cls.generate_otp(length=length, allowed_chars=get_config('user.otp.allowed_chars'))
			new_otp = cls.objects.create(email_or_mobile=email_or_mobile, context=context, otp=code,
			              expires_on=timezone.now() + timedelta(minutes=lifetime))
			return new_otp

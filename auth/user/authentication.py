from django.contrib.auth import get_user_model, backends
from django.core.validators import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

import settings
from labs.exceptions import AuthenticationError, Reason
from labs.fields import validate_email
from .models import Token
from .texts import get_app_text as _t

__author__ = 'chandanojha'


class TokenAuthentication(BaseTokenAuthentication):
	"""
	a substitute for rest_framework.authentication.TokenAuthentication class. It checks the expiry date
	of key as part of validation.
	"""
	model = Token

	def authenticate_credentials(self, key):
		model = self.get_model()
		try:
			token = model.objects.select_related('user').get(key=key)
		except model.DoesNotExist:
			raise AuthenticationError(_t('invalid_token'), reason=Reason.NOT_FOUND)

		if timezone.now().__gt__(token.expiry):
			raise AuthenticationError(_t('token_expired'), reason=Reason.EXPIRED)

		if not token.user.is_active:
			raise AuthenticationError(_t('account_disabled'), reason=Reason.DISABLED)

		return token.user, token


class AuthBackend(backends.ModelBackend):
	"""
	override the authenticate method to implement login mechanism to be used for authentication backend
	"""

	user_model = get_user_model()

	def authenticate(self, request, username=None, password=None, **kwargs):
		user_model = self.user_model
		try:
			if username:
				user = self.find_user(username)
			else:
				user = kwargs.get('user')
				if not user:
					user = user_model.objects.get(**kwargs)
			if user and user.check_password(password):
				return user
		except user_model.DoesNotExist:
			# Run the default password hasher once to reduce the timing
			# difference between an existing and a non-existing user.
			user_model().set_password(password)

	@classmethod
	def find_user(cls, username=None, **kwargs):
		"""
		:param username: This could be an 'email' or 'username'
		:return: 'user' object if found, None otherwise
		"""
		user_model = cls.user_model
		if username is not None:
			try:
				validate_email(username)
				return user_model.objects.get(email=username)
			except DjangoValidationError:
				return user_model.objects.get(**{user_model.USERNAME_FIELD: username})
		return user_model.objects.get(**kwargs)


def find_user(username=None, **kwargs):
	for backend_path in settings.AUTHENTICATION_BACKENDS:
		backend_cls = import_string(backend_path)
		if hasattr(backend_cls, 'find_user'):
			try:
				return getattr(backend_cls, 'find_user')(username=username, **kwargs)
			except:
				pass

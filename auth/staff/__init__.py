from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import ProgrammingError
from django.utils.crypto import get_random_string

from labs.utils import is_migrating, logger


def _get_or_create_bot():
	try:
		bot_user_data = settings.BOT_USER
		bot_email = bot_user_data.get('EMAIL')
	except KeyError as e:
		logger.critical("You need to define 'BOT_USER' details in your settings files: {0}".format(e))
		raise

	from .models import Staff
	try:
		return Staff.objects.select_related('user').get(user__email=bot_email)  # can not use get_or_create
	except Staff.DoesNotExist:
		# user has to be created using create_user manager method so that password is hashed
		kwargs = {
			'username': bot_user_data.get('USERNAME', 'systembot'),
			'email': bot_email,
			'password': get_random_string(length=20),   # No login for BOT, so just use a random pwd nobody will know
			'is_staff': True,
			'first_name': 'Sys',
			'last_name': 'Bot'
		}
		from django.contrib.auth import get_user_model
		user = get_user_model().objects.create_user(**kwargs)
		return Staff.objects.create(user=user, emp_id='0')
	except ProgrammingError:
		pass


_bot_staff = None

def bot_staff():
	if is_migrating():
		return
	global _bot_staff
	if not _bot_staff:
		_bot_staff = _get_or_create_bot()
		setattr(_bot_staff, '_is_bot', None)
	return _bot_staff


def staff_or_none(request_or_user):
	"""
	:param request_or_user: Staff, UserModel or Request
	:return: Staff object if user is a staff, None otherwise
	"""
	user = None
	if isinstance(request_or_user, get_user_model()):
		user = request_or_user     # we have been passed an 'user' object
	elif hasattr(request_or_user, 'user') and isinstance(request_or_user.user, get_user_model()):
		# Here we have Staff or Request each having '.user' in it
		user = request_or_user.user

	return user.staff if user and user.is_staff else None

from django.db import transaction
from django.utils import timezone

import settings
from labs import fields
from labs.exceptions import ServerError
from labs.modelfield import PhoneNumberField
from labs.models import BlankModel
from ..user.models import create_user


def next_emp_id():
	next_id = 1
	staff = Staff.objects.all().last()
	if staff:
		next_id = staff.id + 1
	return timezone.now().strftime("%y%m-") + "{0:03d}".format(next_id)


class Staff(BlankModel):
	user = fields.default_one_to_one_field(settings.AUTH_USER_MODEL)

	emp_id = fields.tiny_char_field(unique=True, default=next_emp_id)
	mobile = PhoneNumberField(null=True, unique=True)
	address = fields.default_text_field()

	public_name = fields.medium_char_field(null=True)

	@property
	def is_active(self):
		return self.user.is_active

	@property
	def is_bot(self):
		return hasattr(self, '_is_bot')

	@property
	def email(self):
		return self.user.email

	@property
	def name(self):
		return self.user.get_full_name()

	@property
	def short_name(self):
		return self.user.get_short_name()

	@property
	def is_superuser(self):
		return self.user.is_superuser

	def save(self, *args, **kwargs):
		if not self.user.is_staff:
			raise ServerError('Creating Staff for is_staff=False?')

		return super().save(*args, **kwargs)

	@property
	def groups(self):
		return self.user.groups.all()

	def has_group(self, names):
		return self.is_active and (self.is_superuser or self.user.groups.filter(name__in=names).exists())

	def has_perm(self, perm, obj=None):
		return self.user.has_perm(perm)

	
def create_staff(email, password, name, **kwargs):
	# get the username from email id (user part)
	username = email and email.split('@')[0]
	if not name:
		# and while we are at it, we also try to guess the name if absent, now this is a bit specific
		# but we assume that email id is in 'firstname + firstletter_of_secondname' form
		name = username[:-1].capitalize() + ' ' + username[-1].capitalize()

	with transaction.atomic():
		user = create_user(email=email, password=password, name=name, is_staff=True, username=username)
		return Staff.objects.create(pk=user.pk, user=user, **kwargs)

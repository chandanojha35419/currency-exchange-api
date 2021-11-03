from django.utils.translation import ugettext_lazy as _



# -------------------------------------
# Easy accessor methods for this app (group=app_label)
#
from labs import texts


def register_app_texts(txt_dict):
	# 'user.staff' means it would inherit all 'texts' from 'user' group as well
	return texts.register_texts('user.staff', txt_dict)


def get_app_text(key, *args, **kwargs):
	return texts.get_text('user.staff', key, *args, **kwargs)


# -------------------------------------
# app-wide texts, note that you can duplicate the following call to register new specific texts close to its usage
#  (in same file or class) as well but make sure that it is not imported before all the models are loaded
#  i.e. django's app-registry is ready.
#
# Duplicate key would be reported at load
#
register_app_texts({
	'invalid_staff_email': _("Invalid email. Please ensure that your email ends with @classicinformatics.com"),
	'cannot_assign_bot': _("Cannot assign BOT user."),
	'user_must_be_staff': _("User must be a staff."),
	'staff_not_active': _("This staff is not active"),
})

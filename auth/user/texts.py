from django.utils.translation import ugettext_lazy as _


__author__ = 'chandanojha'


# -------------------------------------
# Easy accessor methods for this app (group=app_label)
#
from labs import texts


def register_app_texts(txt_dict):
	return texts.register_texts('user', txt_dict)


def get_app_text(key, *args, **kwargs):
	return texts.get_text('user', key, *args, **kwargs)


# -------------------------------------
# app-wide texts, note that you can duplicate the following call to register new specific texts close to its usage
#  (in same file or class) as well but make sure that it is not imported before all the models are loaded
#  i.e. django's app-registry is ready.
#
# Duplicate key would be reported at load
#
register_app_texts({

	'invalid_token': _("Invalid session token, please login again to continue."),
	'token_expired': _("Your session token has expired, please login again to continue."),
	'account_disabled': _("Your account is disabled or deleted, please contact customer care."),
	'need_email_or_mobile': _("Need a valid email id or mobile number as username."),
	'invalid_password': _("Need a valid password."),
	'invalid_first_name': _("First Name allows alphabets and only ,.\'- special characters"),
	'invalid_last_name': _("Last Name allows alphabets and ,.\'- special characters"),
	'invalid_email': _("Invalid email id"),
	'invalid_mobile': _("Invalid mobile number."),
	'invalid_name': _("Invalid name."),
	'auth_user_should_exist': _("Authenticated user should exist by now."),
	'set_auth_user': _("Authenticated user should exist by now, set it in your view or use one of AuthenticatedViewMixin classes"),
	'invalid_username': _("No such user exists."),
	'login_not_allowed': _("You are not allowed to login."),
	'unable_to_login': _("Unable to log in with provided credentials."),
	'otp_sending_failed': _("Could not send OTP, please try again."),
	'user_exists': _("User with given email and/or mobile already exists"),
	'registration_error': _("Error in registration, please try again."),
	'notify_otp_{0}_{1}': _("OTP for verification of _{0}_ is `{1}`."),
	'invalid_staff_email': _("Invalid email. Please ensure that your email ends with @classicinformatics.com"),
	'superuser_password_reset_forbidden': _("Resetting password of other admin or super-user is forbidden."),
	'email_mobile_verified': _("Email and/or Mobile are already verified"),
	'user_does_not_exist': _("User with given email and/or mobile does not exist."),
	'reusing_token': _("Token already exist, reusing."),
	'all_devices_logout': _("Logged out of all devices successfully."),
	'logout': _("Logged out successfully."),
	'pwd_reset_otp': _("Password reset OTP sent to your email."),
	'password_changed': _("Password changed successfully."),
	'verify_account_{0}': _("Sign-up successful. You need to verify your {0} before you can use your account\n\n"),
	'verify_email_or_mobile_{0}': _("Account activated successfully.\n\nPlease take a moment to verify your {0} as well. You can also do it later from inside your profile page."),
	'invalid_otp_{0}': _("Invalid or expired OTP: {0}"),
	'incorrect_username': _("Incorrect username."),
	'incorrect_current_password': _("Incorrect current password."),
	'could_not_change_password': _("Could not change password, please try again."),
	'invalid_user_id': _("Invalid user-id."),
	'invalid_email_mobile': _("Invalid email or mobile."),
	'user_already_active': _("User already active."),
	'invalid_parameter': _("'Invalid or missing parameter: '"),
	'{0}_already_registered': _("This {0} is already registered with us."),
	'cannot_assign_bot': _("Cannot assign BOT user."),
	'user_must_be_staff': _("User must be a staff."),
	'staff_not_active': _("This staff is not active"),

	'user_exists_email_{0}': _("User with email id '{0}' has already signed up."),
})

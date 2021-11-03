import random
import string
# from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.utils import timezone

# from auth.user.models import OTP
from django.core.mail import send_mail


__author__ = 'chandanojha'

# scheduler = BackgroundScheduler()


# scheduler for deleting expired OTPs
# def delete_expired_otps():
#
# 	OTP.objects.filter(expires_on__gt=timezone.now()).delete()
#
#
# scheduler.add_job(delete_expired_otps, 'interval', days=1)
# scheduler.start()
#
#
# # implement for mobile
# def send_otp_mail(mobile, email, event_name, otp_code):
# 	send_mail(
# 		event_name or 'OTP',
# 		'Your OTP is {}.Thank You.'.format(otp_code),
# 		settings.EMAIL_HOST_USER,
# 		[email],
# 		fail_silently=True,
# 	)

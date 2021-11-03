"""
Django settings for mail project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z=xdy4sunp&$&^j+ecnizz(vep7oz-osbt^3()rnl5f$i^5gm4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
AUTH_USER_MODEL = 'user.CustomUser'

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'rest_framework',
	'rest_framework_swagger',
	'rest_framework_filters',
	'auth.user.apps.UserConfig',
	'auth.staff.apps.StaffConfig',
	'currency.apps.CurrencyConfig',
	'corsheaders',

]

AUTHENTICATION_BACKENDS = ['auth.user.authentication.AuthBackend']
REST_FRAMEWORK = {
	'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
	'NON_FIELD_ERRORS_KEY': 'detail',
	'EXCEPTION_HANDLER': 'labs.exceptions.exception_handler',
	'UPLOADED_FILES_USE_URL': False,
	'DEFAULT_FILTER_BACKENDS': [
		'rest_framework_filters.backends.DjangoFilterBackend',
	],

}

# REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ['rest_framework.renderers.JSONRenderer']
SWAGGER_PATH = 'docs/'

SWAGGER_SETTINGS = {
	'USE_SESSION_AUTH': False,
	'SECURITY_DEFINITIONS': {
		"api_key": {
			"type": "apiKey",
			"in": "header",
			"name": "Authorization",
			"value": 'Token staff-swagger-token-741aac85e'
		},
	},
}


DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'HOST': 'localhost',
		'PORT': '5432',
		'NAME': 'scrapper',
		'USER': 'postgres',
		'PASSWORD': 'postgres',
	}
}
MIDDLEWARE = [
	'corsheaders.middleware.CorsMiddleware',
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STATICFILES_DIRS = (
	os.path.join(PROJECT_ROOT, 'static'),
)

STATIC_URL = '/static/'
ANGULAR_URL = '/ng/'

ANGULAR_ROOT = os.path.join(BASE_DIR, 'ngApp/')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'USE THIS EMAIL TO SEND OTP FOR PASSWORD RESET'
EMAIL_HOST_PASSWORD = 'PASSWORD'
BOT_USER = {'USERNAME': 'systembot', 'EMAIL': 'Bot@cli.com'}
CORS_ORIGIN_ALLOW_ALL = True  # If this is used then `CORS_ORIGIN_WHITELIST` will not have any effect
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
	'http://localhost:4200',
]  # If this is used, then not need to use `CORS_ORIGIN_ALLOW_ALL = True`

CORS_ORIGIN_REGEX_WHITELIST = [
	'http://localhost:4200',
]

CORS_ALLOW_HEADERS = [
	'x-requested-with',
	'content-type',
	'accept',
	'origin',
	'authorization',
	'x-csrftoken',
	'user-agent',
	'accept-encoding',
	'cache-control',
	'option'
]

BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'

API_KEY = config('API_KEY')
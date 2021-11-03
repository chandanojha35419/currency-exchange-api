from django.apps import AppConfig


class CurrencyConfig(AppConfig):
	name = 'currency'
	
	def ready(self):
		import currency.celery

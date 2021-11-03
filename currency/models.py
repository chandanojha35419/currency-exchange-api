from django.db import models


class Currency(models.Model):
	from_currency_code = models.CharField(max_length=100, null=False)
	from_currency_name = models.CharField(max_length=100, null=False)
	to_currency_code = models.CharField(max_length=100, null=False)
	to_currency_name = models.CharField(max_length=100, null=False)
	exchange_rate = models.DecimalField(max_digits=20, decimal_places=10)
	last_refreshed = models.DateTimeField()
	timezone = models.CharField(max_length=100, null=False)
	ask_price = models.DecimalField(max_digits=20, decimal_places=10)
	bid_price = models.DecimalField(max_digits=20, decimal_places=10)

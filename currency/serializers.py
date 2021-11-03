from labs.model_serializer import ModelSerializer
from currency.models import *


class CurrencySerializer(ModelSerializer):
	class Meta:
		model = Currency
		fields = '__all__'
		read_only_fields = ('from_currency_name', 'to_currency_name', 'exchange_rate', 'last_refreshed', 'timezone', 'ask_price', 'bid_price')


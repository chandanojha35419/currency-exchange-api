import requests
from currency.celery import app
from currency.models import Currency
from labs.exceptions import ValidationError
from settings import API_KEY


def get_price(from_currency=None, to_currency=None):
	url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={0}&to_currency={1}&apikey={2}".format(
																	from_currency or 'BTC', to_currency or 'USD', API_KEY)
	r = requests.get(url)
	try:
		response_data = r.json()['Realtime Currency Exchange Rate']
		data = {'from_currency_code': response_data['1. From_Currency Code'],
		        'from_currency_name': response_data['2. From_Currency Name'],
		        'to_currency_code': response_data['3. To_Currency Code'],
		        'to_currency_name': response_data['4. To_Currency Name'],
		        'exchange_rate': response_data['5. Exchange Rate'],
		        'last_refreshed': response_data['6. Last Refreshed'],
		        'timezone': response_data['7. Time Zone'],
		        'bid_price': response_data['8. Bid Price'],
		        'ask_price': response_data['9. Ask Price']}
		return Currency.objects.create(**data)
	except KeyError:
		raise ValidationError('Enter valid currency codes.')

@app.task
def get_price_every_hour():
	get_price()



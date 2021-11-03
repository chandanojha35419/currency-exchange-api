# import datetime
# import os
#
# import requests
#
#
# SETTINGS = 'settings'
# os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS
# import django
# django.setup()
#
#
# key = 'TI0EGKLFLPC8WCW6'
#
#
# def get_price(from_currency='y', to_currency='z'):
# 	url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={0}&to_currency={1}&apikey={2}".format(from_currency or 'BTC', to_currency or 'CNY', key)
# 	r = requests.get(url)
# 	try:
# 		response_data = r.json()['Realtime Currency Exchange Rate']
# 		data = {'from_currency_code': response_data['1. From_Currency Code'],
# 		    'from_currency_name':response_data['2. From_Currency Name'],
# 		    'to_currency_code':response_data['3. To_Currency Code'],
# 			'to_currency_name':response_data['4. To_Currency Name'],
# 			'exchange_rate':response_data['5. Exchange Rate'],
# 			'last_refreshed':response_data['6. Last Refreshed'],
# 			'timezone':response_data['7. Time Zone'],
# 			    'bid_price': response_data['8. Bid Price'],
# 		'ask_price':response_data['9. Ask Price']}
# 		# from currency.models import Currency
# 		# return Currency.objects.create(**data)
# 	except KeyError:
# 		from labs.exceptions import ValidationError
# 		raise ValidationError('Enter correct Currency Codes')
# 	print(data)
#
#
# get_price()
# '''
# {'1. From_Currency Code': 'BTC', '2. From_Currency Name': 'Bitcoin', '3. To_Currency Code': 'CNY', '4. To_Currency Name': 'Chinese Yuan', '5. Exchange Rate': '395315.86923900', '6. Last Refreshed': '2021-11-02 06:37:22', '7. Time Zone': 'UTC', '8. Bid Price': '395315.86923900', '9. Ask Price': '395315.93325000'}
# '''


from celery import current_app
current_app.loader.import_default_modules()

tasks = list(sorted(name for name in current_app.tasks if not name.startswith('celery.')))
print(tasks)

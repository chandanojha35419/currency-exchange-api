# currency-exchange-api
Currency exchange api
# currency-exchange-api
Currency exchange api

This Django project retrieves the prices of BTC/USD every hour.
Post method allows us to get prices for any other exchange codes from AlphaAdvantage.
The Api is documented using swagger and uses token based authentication.
The database used is postgres
Celery is being used for scheduling tasks and redis as broker for celery.
Install all the required libraries from requirements.txt file.

use python manage.py migrate for applying migrations

for getting list of tasks scheduled by celery use the following command in the terminal
    celery -A currency.celery worker --loglevel=info


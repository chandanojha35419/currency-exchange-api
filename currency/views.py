from django_filters import FilterSet
from rest_framework.response import Response

from auth.staff.permissions import StaffViewMixin
from currency.main import get_price
from labs.ordering import OrderingMixin
from currency.serializers import *
from labs.views import ListCreateAPIView


class CurrencyFilter(FilterSet):
	class Meta:
		model = Currency
		fields = {
			'from_currency_code': ['exact', 'in', 'startswith', 'icontains'],
			'from_currency_name': ['exact', 'in', 'startswith', 'icontains'],
			'to_currency_code': ['exact', 'in', 'startswith', 'icontains'],
			'to_currency_name': ['exact', 'in', 'startswith', 'icontains'],
			'exchange_rate': ['lte', 'gte'],
			'last_refreshed': ['lte', 'gte'],
			'timezone': ['exact', 'in', 'startswith', 'icontains'],
			'ask_price': ['lte', 'gte'],
			'bid_price': ['lte', 'gte'],
			
		}


class CurrencyView(StaffViewMixin, OrderingMixin, ListCreateAPIView):
	model_class = Currency
	serializer_class = CurrencySerializer
	filter_class = CurrencyFilter
	ordering = '-id'
	
	def perform_create(self, serializer):
		from_currency = serializer.validated_data['from_currency_code']
		to_currency = serializer.validated_data['to_currency_code']

		data = get_price(from_currency, to_currency)
		
		return Response(data=CurrencySerializer(data).data)
	

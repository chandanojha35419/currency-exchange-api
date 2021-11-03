from django.conf.urls import url
from currency import views


urlpatterns = [
    url(r'^quotes/$', views.CurrencyView.as_view(), name='currency-main'),

]

"""mail URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import include

from auth.staff.urls import admin_staff_urlpatterns, staff_urlpatterns
from labs.views.swagger import get_swagger_view


schema_view = get_swagger_view(title="Currency-API")

urlpatterns = [

	url(r'^docs/', schema_view),
	url(r'^api/v1/', include('currency.urls')),

]+admin_staff_urlpatterns+staff_urlpatterns

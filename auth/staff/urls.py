from django.conf.urls import url, include

from ..user.views import AdminPasswordResetView
from ..user.urls import common_urlpatterns as auth_patterns
from ..user.urls import admin_urlpatterns
from . import views

staff_urlpatterns = [
	url(r'^login/$', views.StaffLoginView.as_view(), name='staff-login'),
	url(r'^', include(auth_patterns)),
	url(r'^', include(admin_urlpatterns)),
	url(r'^staffs/detail/(?P<pk>[0-9]+)/$', views.StaffDetailView.as_view(), name='staff-detail'),

]

admin_staff_urlpatterns =[
	url(r'^staffs/$', views.StaffListView.as_view(), name='staff-list'),
	url(r'^staffs/ids/$', views.StaffIdListView.as_view(), name='staff-id-list'),
	url(r'^staffs/(?P<pk>[0-9]+)/$', views.StaffView.as_view(), name='staff-detail-admin'),
	url(r'^staffs/(?P<pk>[0-9]+)/password/$', AdminPasswordResetView.as_view(), name='admin-password-reset'),
]

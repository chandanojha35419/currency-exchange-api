from django.conf.urls import url

from . import views

common_urlpatterns = [
	# url(r'^password/change/$', views.PasswordChangeView.as_view(), name='user-password-change'),
	url(r'^logout/$', views.LogoutView.as_view(), name='user-logout'),
	# url(r'^password/reset-request/$', views.PasswordResetRequestView.as_view(), name='user-password-reset-request'),
	# url(r'^password/reset/$', views.PasswordResetConfirmView.as_view(), name='user-password-reset'),
]

urlpatterns = [
	# url(r'^signup/$', views.SignupView.as_view(), name='user-signup'),
	# url(r'^login/$', views.LoginView.as_view(), name='user-login'),
	# url(r'^$', views.MyUserView.as_view(), name='user-user'),
] + common_urlpatterns

admin_urlpatterns = [
	# url(r'^users/ids/$', views.UserIdListView.as_view(), name='staff-user-ids-list'),
	# url(r'^users/$', views.UserListView.as_view(), name='staff-user-list'),
	# url(r'^users/(?P<pk>[0-9]+)/$', views.UserView.as_view(), name='staff-user-detail'),
	# url(r'^users/(?P<pk>[0-9]+)/password/$', views.AdminPasswordResetView.as_view(), name='admin-password-reset'),
]

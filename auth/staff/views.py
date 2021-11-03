from labs.views import RetrieveUpdateAPIView, ListCreateAPIView, IdListAPIView, RetrieveAPIView
from .permissions import StaffViewMixin, ManagerViewMixin
from .serializers import StaffSerializer
from ..staff.models import Staff
from ..user.serializers import LoginSerializer
from ..user.views import LoginView


class StaffLoginView(LoginView):
	class MySerializer(LoginSerializer):
		def is_login_allowed(self, user):
			return user.is_staff


# Non-Admin Staff detail View
class StaffDetailView(StaffViewMixin, RetrieveAPIView):
	model_class = Staff
	serializer_class = StaffSerializer


# --- Manager Only ----
#
class StaffListViewMixin(ManagerViewMixin):
	model_class = Staff
	ordering = ('-id',)
	
	def get(self, request, *args, **kwargs):
		"""
		return a list of all the Staffs.
		---
		parameters:
			- name: depth
			  description: nesting level for profile.
			  type: integer
			  paramType: query
			- name: search
			  description: string to be looked for.
			  type: string
			  paramType: query
			- name: mode
			  description: mode in which the search will be carried out. It can be set to 'exact' to get \
			  exact match of the search term.
			  type: string
			  paramType: query
			- name: ordering
			  description: field name used for ordering of search result. options are username, first_name \
			  last_name, email, mobile
			  type: string
			  paramType: query
		"""
		return super().get(request, *args, **kwargs)


class StaffListView(StaffListViewMixin, ListCreateAPIView):
	serializer_class = StaffSerializer


class StaffIdListView(StaffListViewMixin, IdListAPIView):
	pass


class StaffView(ManagerViewMixin, RetrieveUpdateAPIView):
	model_class = Staff
	serializer_class = StaffSerializer


class PermissionStaffListView(StaffIdListView):
	def filter_queryset(self, queryset):
		permsision = self.kwargs['pk']
		q1 = super().filter_queryset(queryset).filter(user__user_permissions__id=permsision)
		q2 = super().filter_queryset(queryset).filter(user__groups__permissions__id=permsision)
		return q1.union(q2)

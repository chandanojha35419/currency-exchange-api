from django.conf import settings

from labs.utils import load_class_from_string
from ..user import permissions


class IsStaff(permissions.IsStaff):
	"""
	permission class to set staff permission.
	"""
	
	def has_permission(self, request, view):
		return super().has_permission(request, view) and request.user.staff


class IsAdmin(IsStaff):
	"""
	permission class to set staff permission.
	"""
	
	def has_permission(self, request, view):
		return super().has_permission(request, view) and request.user.is_superuser


class Manager(IsStaff):
	def has_permission(self, request, view):
		return super().has_permission(request, view) and \
			   (request.user.is_superuser or request.user.staff.has_group(('manager', 'ADMIN')))


class StaffViewMixin(permissions.AuthenticatedViewMixin):
	permission_classes = (IsStaff,)
	
	def perform_authentication(self, request):
		""" We override because we want to set our 'staff'"""
		super().perform_authentication(request)
		
		# 'user' may not have 'staff' in case of invalid token (AnonymousUser).
		if hasattr(request.user, 'staff'):
			setattr(request, 'staff', request.user.staff)


class ManagerViewMixin(StaffViewMixin):
	permission_classes = (Manager,)


class AdminOnlyViewMixin(StaffViewMixin):
	permission_classes = (IsAdmin,)


def get_staff_view_mixin(app_label):
	"""
	Helper function to return appropriate 'StaffViewMixin' for given app_label. It checks if we have any specific
	permission classes specified for this app in project settings, creates and return a subclass with given permission on
	the fly. If nothing found then it uses the default 'StaffViewMixin' class (above) which just checks for user.is_staff
	:param app_label:
	:return:
	"""
	permissions = hasattr(settings, 'APP_STAFF_PERMISSIONS') and settings.APP_STAFF_PERMISSIONS.get(app_label)
	if permissions and isinstance(permissions, (tuple, list)):
		permissions = [load_class_from_string(p) for p in permissions]
		return type(str('StaffViewMixin_' + app_label), (StaffViewMixin,), {'permission_classes': permissions})
	else:
		return StaffViewMixin

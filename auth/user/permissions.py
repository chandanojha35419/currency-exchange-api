from rest_framework.permissions import IsAuthenticated

from .authentication import TokenAuthentication

__author__ = 'chandanojha'


class IsStaff(IsAuthenticated):
	"""
	permission class to set staff permission.
	"""
	def has_permission(self, request, view):
		return super().has_permission(request, view) and request.user.is_staff


class IsAdmin(IsStaff):
	"""
	permission class to set staff permission.
	"""
	def has_permission(self, request, view):
		return super().has_permission(request, view) and request.user.is_superuser


class AuthenticatedViewMixin(object):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)


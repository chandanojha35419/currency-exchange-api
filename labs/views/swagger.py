from django.conf import settings
from rest_framework import exceptions
from rest_framework.permissions import AllowAny
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework.views import APIView

from rest_framework_swagger import renderers

from auth.staff.views import StaffViewMixin
from auth.user import permissions


class SwaggerViewMixin(permissions.AuthenticatedViewMixin):
	permission_classes = [AllowAny]

	def perform_authentication(self, request):
		""" We override because we want to DETECT and set our 'staff' """
		super().perform_authentication(request)

		# 'user' may not have 'staff' in case of invalid token (AnonymousUser)
		if request and request.user.is_authenticated:
			if request.user.is_staff:
				setattr(request, 'staff', request.user.staff)
			else:
				setattr(request, 'staff', request.user.staff)


def get_swagger_view(title=None, url=None, patterns=None, urlconf=None, authentication_mixin=StaffViewMixin):
	"""
	Returns schema view which renders Swagger/OpenAPI.
	"""

	class Generator(SchemaGenerator):
		"""
		SchemaGenerator.create_view clones the request leaving out our 'staff' attribute,
		 so we override to insert it back
		"""
		def create_view(self, callback, method, request=None):
			view = super().create_view(callback, method, request=request)
			if view.request:
				if hasattr(request, 'staff'):
					setattr(view.request, 'staff', request.staff)
			return view
		
	def detect_hosted_path(request):
		# Try to detect the 'path' on which we are hosted
		# so if we are hosted at 'http://abcd.com/some/path/' and our SWAGGER_PATH is '/docs' under that
		# then we would get '/some/path/docs/' as the request.path and after stripping SWAGGER_PATH we would
		# be left with '/some/path'
		if request.path.endswith(settings.SWAGGER_PATH):
			path = request.path[:-len(settings.SWAGGER_PATH)]
			if path and path != '/':
				return path
		return None

	class SwaggerSchemaView(authentication_mixin, APIView):
		permission_classes = [AllowAny]
		schema = None       # Exclude us!

		_ignore_model_permissions = True
		renderer_classes = [
			CoreJSONRenderer,
			renderers.OpenAPIRenderer,
			renderers.SwaggerUIRenderer
		]

		def get(self, request):
			generator = Generator(
				title=title,
				url=url or detect_hosted_path(request),
				patterns=patterns,
				urlconf=urlconf
			)
			schema = generator.get_schema(request=request)

			if not schema:
				raise exceptions.ValidationError(
					'The schema generator did not return a schema Document'
				)

			return Response(schema)

	return SwaggerSchemaView.as_view()

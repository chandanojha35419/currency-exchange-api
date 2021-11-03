from .generics import RetrieveAPIView, ListAPIView, IdListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView,\
	ListCreateAPIView, RetrieveUpdateAPIView, RetrieveDestroyAPIView, UpdateDestroyAPIView, \
	CreateDestroyAPIView, RetrieveUpdateDestroyAPIView

from rest_framework.settings import api_settings


def auto_schema(manual_fields):
	"""
	Wraps coreapi.AutoSchema usage so that the same will work if we switch to OpenAPI instead.

	:param manual_fields: List of additional fields to be included when using coreapi.AutoSchema
	:return:
	"""
	auto_schema_class = api_settings.DEFAULT_SCHEMA_CLASS
	try:
		# See if the settings says to use coreapi.AutoSchema, which takes 'manual_fields' as argument
		import coreapi

		if isinstance(manual_fields, dict):
			# We allow manual_fields to be a dictionary of {'request_method': [fields array]} so that schema fields
			# can be varied as per request method (.e.g: including some fields in POST only)
			manual_fields = {k: [coreapi.Field(**field_kw) for field_kw in v] for k, v in manual_fields.items()}
			class AutoSchema(auto_schema_class):
				def get_manual_fields(self, path, method):
					return super().get_manual_fields(path, method).get(method, [])
			auto_schema_class = AutoSchema
		else:
			manual_fields = [coreapi.Field(**field_kw) for field_kw in manual_fields]

		return auto_schema_class(manual_fields=manual_fields)
	except (TypeError, ImportError):
		# No, most probably openapi.AutoSchema which doesn't accept any param
		return auto_schema_class()

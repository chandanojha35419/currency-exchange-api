from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import QuerySet
from django.views.generic.base import ContextMixin
from labs.exceptions import ValidationError

__author__ = 'chandanojha'


class OrderingMixin(ContextMixin):
	"""A mixin for views for ordering in the models."""
	allow_empty = True
	queryset = None
	model = None
	context_object_name = None
	ordering = None

	def model_field_exists(self, field):
		try:
			model = self.model
			if type(field) != str:
				raise ValidationError('Error in mentioning of default ordering field for the model {0}.use string value ONLY'.format(model.__name__))
			if field.startswith('-'):
				field = field[1:]
			model._meta.get_field(field)
			return True
		except models.FieldDoesNotExist:
			return False

	def get_queryset(self):
		"""
		Return the list of items for this view.
		The return value must be an iterable and may be an instance of
		`QuerySet` in which case `QuerySet` specific behavior will be enabled.
		"""
		self.model = self.__class__.model_class
		if self.queryset is not None:
			queryset = self.queryset
			if isinstance(queryset, QuerySet):
				queryset = queryset.all()
		elif self.model is not None:
			queryset = self.model._default_manager.all()
		else:
			raise ImproperlyConfigured(
				"%(cls)s is missing a QuerySet. Define "
				"%(cls)s.model, %(cls)s.queryset, or override "
				"%(cls)s.get_queryset()." % {
					'cls': self.__class__.__name__
				}
			)
		ordering = self.request.query_params.get('ordering')
		if not ordering:
			ordering = self.get_ordering() or 'id'
		if not self.model_field_exists(ordering):
			raise ValidationError('Select a valid field for ordering.')
		if isinstance(ordering, str):
				ordering = (ordering,)
		queryset = queryset.order_by(*ordering)

		return queryset

	def get_ordering(self):
		"""Return the field or fields to use for ordering the queryset."""
		return self.ordering
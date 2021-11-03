import logging

from django.db import models, IntegrityError
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import utils
from ..exceptions import (ValidationError, NotFound, Forbidden, AuthenticationError, ServiceUnavailable, ServerError,
						  friendly_integrity_error, bot_error)

__author__ = 'chandanojha'

from ..generics import EmptySerializer

from ..pagination import BOTPagination

logger = logging.getLogger(__name__)


# ----
# Decorator for adding exception handling in any view method. To be used with the top-level view methods i.e.
# get/retrieve/list, post/create, patch/update, delete/destroy

def view_exception_handler(view_method):
	def decorator(self, request, *args, **kwargs):
		try:
			return view_method(self, request, *args, **kwargs)
		except (ValidationError, AuthenticationError, NotFound, Forbidden, ServiceUnavailable, ServerError) as e:
			return e.response(logger=logger.info)
		
		except exceptions.ValidationError as e:
			return bot_error(e, ValidationError).response(logger=logger.info)
		except exceptions.NotFound as e:
			return bot_error(e, NotFound).response(logger=logger.info)
		except exceptions.PermissionDenied as e:
			return bot_error(e, Forbidden).response(logger=logger.warn)
		except exceptions.APIException as e:
			return bot_error(e, ServerError).response(logger=logger.exception)
		
		except model_does_not_exists(self) as e:
			return NotFound(detail=e).response(logger=logger.warn)
		except Http404 as e:
			return NotFound(detail=e).response(logger=logger.info)
		
		except IntegrityError as e:
			return friendly_integrity_error(e).response(logger.warn)
		
		except Exception as e:
			return bot_error(e).response(logger=logger.exception)
	
	return decorator


def model_does_not_exists(view):
	if getattr(view, 'model_class', None):
		return view.model_class.DoesNotExist
	
	class DummyException(Exception):
		pass
	
	return DummyException


def get_class_name(instance):
	import re
	cls = getattr(instance, 'model_class', None)
	if cls:
		return cls.__name__
	
	class_name = instance.__class__.__name__
	return re.sub('View', '', class_name)


class GetQuerySetMixin(object):
	def get_queryset(self):
		if self.queryset is not None:
			return super().get_queryset()
		
		return self.model_class and self.model_class.objects.all().order_by(self.model_class._meta.pk.attname)
	
	def get_object(self):
		try:
			return super().get_object()
		except Http404 as e:
			model_name = (self.model_class and self.model_class.__name__) or 'Resource'
			raise Http404("Not found: {model} with {lookup_field} {value}. Actual Exception {detail}".format(
				model=model_name, lookup_field=self.lookup_field,
				value=self.kwargs[self.lookup_url_kwarg or self.lookup_field], detail=e))


class GetModelMixin(GetQuerySetMixin):
	model_class = None
	
	def get_requested_depth(self, request=None):
		depth = utils.query_param(request or self.request, 'depth')
		if depth is not None:
			try:
				depth = int(depth)
				return min(max(depth, 0), 5)
			except ValueError:
				pass
	
	def get_serializer(self, *args, **kwargs):
		# See if client has requested only specific fields
		fields = utils.query_param(self.request, 'fields')
		if fields:
			kwargs['fields'] = utils.str_list(fields)
		
		# Set the depth for serializer if requested
		depth = self.get_requested_depth()
		if depth is not None:
			kwargs['depth'] = depth
		return super().get_serializer(*args, **kwargs)


class RetrieveModelMixin(GetModelMixin):
	"""
	Retrieve a model instance.
	"""
	
	def retrieve_or_raise(self, request, *args, **kwargs):
		""" Same as DRF.mixins.RetrieveModelMixin.retrieve() """
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		return Response(serializer.data)
	
	@view_exception_handler
	def retrieve(self, request, *args, **kwargs):
		return self.retrieve_or_raise(request, *args, **kwargs)


class ListModelMixin(GetModelMixin):
	"""
	List a queryset.
	"""
	pagination_class = BOTPagination
	
	def list_or_raise(self, request, *args, **kwargs):
		""" Same as DRF.mixins.RetrieveModelMixin.list() """
		queryset = self.filter_queryset(self.get_queryset())
		
		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)
	
	@view_exception_handler
	def list(self, request, *args, **kwargs):
		return self.list_or_raise(request, *args, **kwargs)
	
	def filter_queryset(self, queryset):
		"""
		List of objects in comma separated ids
		"""
		queryset = super().filter_queryset(queryset)
		
		ids = utils.int_list(utils.query_param(self.request, 'ids'))
		if ids is not None:
			queryset = queryset.filter(pk__in=set(ids))
		
		return queryset


class IdListModelMixin(ListModelMixin):
	serializer_class = EmptySerializer
	
	def filter_queryset(self, queryset):
		queryset = super().filter_queryset(queryset)
		return queryset.values_list('pk', flat=True)
	
	def list_or_raise(self, request, *args, **kwargs):
		# No serializing..
		queryset = self.filter_queryset(self.get_queryset())
		
		page = self.paginate_queryset(queryset)
		if page is not None:
			return self.get_paginated_response(page)
		
		return Response(list(queryset))
	
	def list(self, request, *args, **kwargs):
		response = super().list(request, *args, **kwargs)
		
		# check for success response before wrapping data to ids
		if response.status_code == 200:
			# Wrap the data inside 'ids' field, so [1,2,3] becomes {"ids":[1,2,3]}
			response.data = {'ids': response.data}
		return response


class CreateUpdateMixinBase(object):
	def get_response_serializer_class(self):
		return self.serializer_class  # Return different serializer as needed
	
	# Fix #781: Removed 'serializer' parameter and reuse of incoming request data (serializer.data)
	# for sending back as response if response_serializer is not different to incoming one.
	# Now we always serialize the instance again
	#
	# We also try to send the instance 'as is' if it is neither a Response() nor a Model(), hoping that
	# it is still JSON serializable (most probably a dictionary or list)
	def get_success_response(self, instance):
		if instance is None:
			return Response()
		elif isinstance(instance, Response):
			return instance
		elif isinstance(instance, models.Model):
			serializer_class = self.get_response_serializer_class()
			return Response(serializer_class(instance).data)
		
		# Neither a 'Response()' nor a 'Model()', still send it, hopefully it is JSON serializable at least..
		return Response(instance)
	
	def validate(self, serializer, raise_exception=True):
		""" So that subclass can override it and handle the serializer exception if needed """
		return serializer.is_valid(raise_exception=raise_exception)


class CreateModelMixin(CreateUpdateMixinBase):
	
	def create_or_raise(self, request, request_data=None, *args, **kwargs):
		serializer = self.get_serializer(data=request_data or request.data)
		self.validate(serializer, raise_exception=True)
		new_instance = self.perform_create(serializer)  # new_instance may not be actual model for non-model serializers
		if new_instance:
			return self.get_success_response(new_instance)
		
		return ServerError().response(logger=logger.error)
	
	@view_exception_handler
	def create(self, request, *args, **kwargs):
		return self.create_or_raise(request, *args, **kwargs)
	
	def perform_create(self, serializer):
		"""
		Unlike rest_framework.mixins.CreateModelMixin.preform_create, this returns the created object
		"""
		return serializer.save()


class UpdateModelMixin(GetQuerySetMixin, CreateUpdateMixinBase):
	"""
	Update a model instance.
	"""
	http_method_names = tuple(set(APIView.http_method_names) - {'put'})  # one liner 'NoPutMixin' :-)
	
	def update_or_raise(self, request, request_data=None, *args, **kwargs):
		partial = kwargs.pop('partial', False)
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request_data or request.data, partial=partial)
		
		self.validate(serializer, raise_exception=True)
		updated_instance = self.perform_update(
			serializer)  # new_instance may not be actual model for non-model serializers
		
		if getattr(instance, '_prefetched_objects_cache', None):
			# If 'prefetch_related' has been applied to a queryset, we need to
			# forcibly invalidate the prefetch cache on the instance.
			instance._prefetched_objects_cache = {}
		
		if updated_instance:
			return self.get_success_response(updated_instance)
		
		return ServerError().response(logger=logger.error)
	
	@view_exception_handler
	def update(self, request, *args, **kwargs):
		return self.update_or_raise(request, *args, **kwargs)
	
	def perform_update(self, serializer):
		"""
		Unlike rest_framework.mixins.UpdateModelMixin.preform_update, this returns the updated object
		"""
		return serializer.save()
	
	def partial_update(self, request, *args, **kwargs):
		kwargs['partial'] = True
		return self.update(request, *args, **kwargs)


class DestroyModelMixin(GetQuerySetMixin):
	"""
	Destroy a model instance.
	"""
	
	def destroy_or_raise(self, request, *args, **kwargs):
		instance = self.get_object()
		result = self.perform_destroy(instance)
		if result:
			if isinstance(result, Response):
				return result
			
			return Response(status=status.HTTP_204_NO_CONTENT)
		return ServerError().response(logger=logger.error)
	
	@view_exception_handler
	def destroy(self, request, *args, **kwargs):
		return self.destroy_or_raise(request, *args, **kwargs)
	
	def perform_destroy(self, instance):
		try:
			return instance.delete()
		except models.ProtectedError as e:
			raise Forbidden(_("{0} `{1}` can not be deleted since it has references elsewhere.").format(
				get_class_name(instance), instance), detail=e)


class NestedResourceParentViewMixin:
	"""
	Mixin for handling /parent-resource/{pk}/some-resource(s) type of views where the accessed resource
	# is restricted to that of parent's

	Subclass may override get_parent_id() to use kwarg other than {pk}
	"""
	parent_model = None
	parent_field_name = None
	parent_url_lookup_field = None
	
	def get_parent_field_name(self, suffix=''):
		f = getattr(self, '_parent_class_field', None)
		if not f:
			f = self.parent_field_name or utils.camel_to_snakecase(self.parent_model.__name__)
			setattr(self, '_parent_class_field', f)
		return f + suffix if suffix else f
	
	def get_parent_id(self):
		try:
			return self.kwargs[self.parent_url_lookup_field or self.lookup_field]
		except KeyError:
			return None
	
	def get_parent_filter_kwarg(self):
		return {self.get_parent_field_name(suffix='_id'): self.get_parent_id()}
	
	def get_parent(self):
		parent_id = self.get_parent_id()
		try:
			return self.parent_model.objects.get(pk=parent_id) if parent_id else None
		except self.parent_model.DoesNotExist:
			raise NotFound()
	
	def filter_queryset(self, queryset):
		return super().filter_queryset(queryset.filter(**self.get_parent_filter_kwarg()))
	
	def get_serializer_context(self):
		""" Let's set the incoming 'parent' in the context so that it is available in serializer """
		ctx = super().get_serializer_context()
		ctx[self.get_parent_field_name()] = self.get_parent()
		return ctx
	
	def validate(self, serializer, raise_exception=True):
		""" So that we can auto-set 'parent' field """
		ret = serializer.is_valid(raise_exception=raise_exception)
		if ret:
			field = self.get_parent_field_name()
			if '__' not in field and field not in serializer.validated_data:
				# '__' means it is not immediate parent, so we can not set it
				serializer.validated_data[field] = serializer.context[field]  # see get_serializer_context() above
		return ret

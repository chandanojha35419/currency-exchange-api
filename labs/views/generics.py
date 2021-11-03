import logging

from django.conf import settings
from rest_framework import generics

from .mixins import (RetrieveModelMixin, ListModelMixin, IdListModelMixin,
                     CreateModelMixin, UpdateModelMixin, DestroyModelMixin, get_class_name)

__author__ = 'chandanojha'

from ..exceptions import bot_error

logger = logging.getLogger(__name__)


class RetrieveAPIView(RetrieveModelMixin, generics.GenericAPIView):
	"""
	Subclass must define followings:

	model_class = SubclassModel
	serializer_class = SubclassSerializer   # or implement get_serializer_class()
	"""
	def get(self, request, *args, **kwargs):
		"""
		Return the object identified by `pk`.
		---
		parameters:
			- name: depth
			  description: nesting level for the object, default=0
			  type: integer
			  paramType: query
		"""
		try:
			if logger.isEnabledFor(logging.DEBUG):
				logger.debug('{0}  {1}?{2} => model={3}, pk={4}'.format(
					request.method, request.path, request.query_params.dict(), get_class_name(self), kwargs.get('pk')))

			response = self.retrieve(request, *args, **kwargs)
			return response if settings.DEBUG else self.add_caching_headers(response)

		except Exception as e:
			return bot_error(e).response(logger=logger.exception)

	@classmethod
	# Override this method in your view if you want your response to be cached by client.
	def add_caching_headers(cls, response):
		return response


class ListAPIView(ListModelMixin, generics.GenericAPIView):
	"""
	Subclass must define followings:

	model_class = SubclassModel
	serializer_class = SubclassSerializer   # or implement get_serializer_class()
	"""
	def get(self, request, *args, **kwargs):
		"""
		Return paginated list of objects

		Response Headers:
			total_items: Count of total objects returned
			page_size: No. of objects in a page
		---
		parameters:
			- name: depth
			  description: nesting level for the object, default=0
			  type: integer
			  paramType: query

			- name: page
			  description: Page no. to navigate to, default=1).
			  type: integer
			  paramType: query

			- name: page_size
			  description: No. of objects to be returned in a page, default=20 (CONST.PAGE_SIZE)
			  type: integer
			  paramType: query

			- name: ids
			  description: Comma separated ids of requested objects
			  type: string
			  paramType: query
		"""
		try:
			if logger.isEnabledFor(logging.DEBUG):
				logger.debug('{0}  {1}?{2} => model={3}'.format(
					request.method, request.path, request.query_params.dict(), get_class_name(self)))

			response = self.list(request, *args, **kwargs)
			return response if settings.DEBUG else self.add_caching_headers(response)

		except Exception as e:
			return bot_error(e).response(logger=logger.exception)

	@classmethod
	# Override this method in your view if you want your response to be cached by client.
	def add_caching_headers(cls, response):
		return response


class IdListAPIView(IdListModelMixin, ListAPIView):
	pass


class CreateAPIView(CreateModelMixin, generics.GenericAPIView):
	"""
	Concrete view for creating an instance, exactly like generics.CreateAPIView, but uses our own mixin
	Subclass should override perform_create to do actual work. Note that perform_create should return created
	instance unlike super's mixins.CreateModelMixin.perform_create which returns nothing
	"""
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)


class ListCreateAPIView(CreateModelMixin, ListAPIView):
	"""
	Concrete view for listing a queryset or creating a model instance.
	"""
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)


class UpdateAPIView(UpdateModelMixin, generics.GenericAPIView):
	"""
	Concrete view for updating a model instance.
	"""
	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return self.partial_update(request, *args, **kwargs)


class DestroyAPIView(DestroyModelMixin, generics.GenericAPIView):
	"""
	Concrete view for retrieving or deleting a model instance.
	"""
	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)


class RetrieveUpdateAPIView(UpdateModelMixin, RetrieveAPIView):
	"""
	Concrete view for retrieving, updating a model instance.
	"""
	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(DestroyModelMixin, RetrieveAPIView):
	"""
	Concrete view for retrieving or deleting a model instance.
	"""
	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)


class UpdateDestroyAPIView(DestroyModelMixin, UpdateAPIView):
	"""
	Concrete view for updating and deleting a model instance.
	"""
	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)


class CreateDestroyAPIView(DestroyModelMixin, CreateAPIView):
	"""
	Concrete view for creating and deleting a model instance.
	"""
	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(UpdateModelMixin, DestroyModelMixin, RetrieveAPIView):
	"""
	Concrete view for retrieving, updating or deleting a model instance.
	"""
	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return self.partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		return self.destroy(request, *args, **kwargs)


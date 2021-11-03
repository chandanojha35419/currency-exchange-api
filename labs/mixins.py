from django.db import models
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from labs import utils
from labs.exceptions import ServerError, Forbidden, view_exception_handler
from labs.generics import GetQuerySetMixin, GetModelMixin
from labs.pagination import BOTPagination
from labs.utils import logger, get_class_name
from django.utils.translation import ugettext_lazy as _

__author__ = 'chandanojha'


class CreateUpdateMixinBase(object):
    def get_response_serializer_class(self):
        return self.serializer_class  # Return different serializer as needed

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

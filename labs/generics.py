from django.http import Http404
from rest_framework import serializers, status, response
from rest_framework.response import Response
from rest_framework.views import APIView

from labs import utils
from labs.exceptions import view_exception_handler
from labs.model_serializer import ModelSerializer

__author__ = 'chandanojha'


# one liner 'NoPutMixin' :-)
class AllowedMethodsMixin:
    http_method_names = tuple(set(APIView.http_method_names) - {'put'})


# for creating a readonly view
class ReadOnlySerializerMixin:
    def update(self, instance, validated_data):
        assert False, "Attempting write operation on read-only serializer"

    def create(self, validated_data):
        assert False, "Attempting write operation on read-only serializer"

    def save(self, **kwargs):
        assert False, "Attempting write operation on read-only serializer"


class ReadOnlySerializer(ReadOnlySerializerMixin, serializers.Serializer):
    pass


class ReadOnlyModelSerializer(ReadOnlySerializerMixin, ModelSerializer):
    pass


# use this when serializer is not required
EmptySerializer = ReadOnlySerializer


# use this method for replacing get_queryset method in views

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


def success_response(message, detail=None, code=status.HTTP_200_OK):
    """
    Wrapper for quickly creating success response
    :param message: success message to be passed to client
    :param detail: any extra details if any
    :param code: success code (2xx series)
    :return: Http Response object
    """
    message = message or 'Success'
    res = {'code': code, 'message': message}
    if detail:
        res['detail'] = detail
    return response.Response(res, status=code)


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


class ListModelMixin(GetModelMixin):
    """
    List a queryset.
    """

    def list_or_raise(self, request, *args, **kwargs):
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


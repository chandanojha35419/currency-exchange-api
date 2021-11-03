from collections import OrderedDict

from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.db.models.query import EmptyQuerySet
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
__author__ = 'chandanojha'


class BOTPaginatorClass(Paginator):

    def validate_number(self, number):
        """
        Validates the given 1-based page number.
        """
        try:
            number = int(float(number))  # provides support for float-type page numbers
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number


class BOTPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    page_size = 20
    django_paginator_class = BOTPaginatorClass

    def paginate_queryset(self, queryset, request, view=None):
        if isinstance(queryset, EmptyQuerySet):
            # Do not try to paginate an empty queryset (like one returned by queryset.none())
            # otherwise Django paginator issues a warning of it not being ordered
            #
            # Note that in this case self.page will not be initialized and will throw AttributeError
            # Not initializing these (like super's paginate_queryset call does) will throw AttributeError later
            self.page = None
            self.request = request
            return queryset
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        """
        Return a paginated `Response` with pagination information in header
        This is different from default which returns the info as part of response with actual
        data in a 'result' container
        """

        # Normally if we are here then self.page should exist but in case of EmptyQuerySet (see paginate_queryset() above)
        # no actual pagination is done and we will have self.page as None
        count = self.page.paginator.count if self.page else 0
        headers = OrderedDict([
            ('total_items', count),
            ('page_size', self.get_page_size(self.request)),
        ])
        return Response(data, status=status.HTTP_200_OK, headers=headers)

# This is here just to enable the caller to import everything from here
from labs.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from labs.views import CreateAPIView as BaseCreateAPIView, ListCreateAPIView as BaseListCreateAPIView, \
    UpdateAPIView as BaseUpdateAPIView, DestroyAPIView as BaseDestroyAPIView, \
    RetrieveUpdateAPIView as BaseRetrieveUpdateAPIView, RetrieveDestroyAPIView as BaseRetrieveDestroyAPIView, \
    UpdateDestroyAPIView as BaseUpdateDestroyAPIView, CreateDestroyAPIView as BaseCreateDestroyAPIView, \
    RetrieveUpdateDestroyAPIView as BaseRetrieveUpdateDestroyAPIView


class CreateAPIView(CreateModelMixin, BaseCreateAPIView):
    pass


class ListCreateAPIView(CreateModelMixin, BaseListCreateAPIView):
    pass


class UpdateAPIView(UpdateModelMixin, BaseUpdateAPIView):
    pass


class DestroyAPIView(DestroyModelMixin, BaseDestroyAPIView):
    pass


class RetrieveUpdateAPIView(UpdateModelMixin, BaseRetrieveUpdateAPIView):
    pass


class RetrieveDestroyAPIView(DestroyModelMixin, BaseRetrieveDestroyAPIView):
    pass


class UpdateDestroyAPIView(UpdateModelMixin, DestroyModelMixin, BaseUpdateDestroyAPIView):
    pass


class CreateDestroyAPIView(CreateModelMixin, DestroyModelMixin, BaseCreateDestroyAPIView):
    pass


class RetrieveUpdateDestroyAPIView(UpdateModelMixin, DestroyModelMixin, BaseRetrieveUpdateDestroyAPIView):
    pass

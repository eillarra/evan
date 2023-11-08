from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Event

from .permissions import EventRelatedPermission


class EventCreateModelMixin(CreateModelMixin):
    def perform_create(self, serializer):
        serializer.save(event=Event.objects.get(code=self.kwargs.get("code")))


class EventListModelMixin(ListModelMixin):
    @method_decorator(never_cache)
    def list(self, request, *args, **kwargs):
        event_id = Event.objects.values_list("id", flat=True).get(code=self.kwargs.get("code"))
        self.queryset = self.queryset.filter(event_id=event_id)
        return super().list(request, *args, **kwargs)


class EventRelatedViewSet(EventListModelMixin, EventCreateModelMixin, GenericViewSet):
    permission_classes = [EventRelatedPermission]
    pagination_class = None

    def get_event(self):
        if not hasattr(self, "_event"):
            self._event = Event.objects.get(code=self.kwargs.get("code"))
        return self._event


class EventRelatedCreateOnlyViewSet(EventCreateModelMixin, GenericViewSet):
    permission_classes = [EventRelatedPermission]


class EventRelatedListOnlyViewSet(EventListModelMixin, GenericViewSet):
    permission_classes = [EventRelatedPermission]

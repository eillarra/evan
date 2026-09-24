from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Event

from .permissions import EventRelatedPermission


def module_enabled_lookup(module: str, *, prefix: str = "event") -> dict[str, bool]:
    """Build a JSON path lookup matching objects whose event has a module enabled.

    :param module: The module key to filter on.
    :param prefix: The ORM path prefix to the event for the filtered model.
    :returns: A single-entry kwargs dict for queryset filtering.
    """
    return {f"{prefix}__config__modules__{module}": True}


class EventCreateModelMixin(CreateModelMixin):
    def perform_create(self, serializer):
        event = Event.objects.get(code=self.kwargs.get("code"))
        module_key = getattr(self, "module_key", None)

        if module_key and not event.module_enabled(module_key):
            raise PermissionDenied(f"The '{module_key}' module is not enabled for this event.")

        serializer.save(event=event)


class EventListModelMixin(ListModelMixin):
    """List mixin for event-scoped viewsets, honouring the module toggles.

    When ``module_key`` is set, events with that module disabled yield an empty
    list, before permissions are consulted.
    """

    module_key: str | None = None

    @method_decorator(never_cache)
    def list(self, request, *args, **kwargs):
        event_id = Event.objects.values_list("id", flat=True).get(code=self.kwargs.get("code"))
        self.queryset = self.queryset.filter(event_id=event_id)

        if self.module_key:
            self.queryset = self.queryset.filter(**module_enabled_lookup(self.module_key))

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

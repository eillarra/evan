from django.views.decorators.cache import never_cache
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.schemas import AutoSchema
from rest_framework.viewsets import GenericViewSet

from evan.models import Event
from .permissions import EventRelatedPermission
from .schema import event_code_field


class EventCreateModelMixin(CreateModelMixin):
    def perform_create(self, serializer):
        serializer.save(event=Event.objects.get(code=self.kwargs.get('code')))


class EventListModelMixin(ListModelMixin):
    @never_cache
    def list(self, request, *args, **kwargs):
        event_id = Event.objects.values_list('id', flat=True).get(code=self.kwargs.get('code'))
        self.queryset = self.queryset.filter(event_id=event_id)
        return super().list(request, *args, **kwargs)


class EventRelatedViewSet(EventListModelMixin, EventCreateModelMixin, GenericViewSet):
    permission_classes = (EventRelatedPermission,)
    pagination_class = None
    schema = AutoSchema(manual_fields=[event_code_field])


class EventRelatedCreateOnlyViewSet(EventCreateModelMixin, GenericViewSet):
    permission_classes = (EventRelatedPermission,)
    schema = AutoSchema(manual_fields=[event_code_field])

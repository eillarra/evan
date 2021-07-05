from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Event
from ..permissions import EventPermission, EventAttendeePermission
from ..serializers import AttendeeSerializer, EventSerializer


class EventViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "code"
    permission_classes = (EventPermission,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.prefetch_related("topics", "tracks", "fees", "sessions__topics", "venues__rooms")
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["get"],
        pagination_class=None,
        permission_classes=(EventAttendeePermission,),
        serializer_class=AttendeeSerializer,
    )
    @never_cache
    def attendees(self, request, *args, **kwargs):
        self.queryset = (
            get_user_model().objects.filter(registrations__event_id=self.get_object().id).select_related("profile")
        )
        return ListModelMixin.list(self, request, *args, **kwargs)

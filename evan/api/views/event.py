from django.views.decorators.cache import never_cache
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Event
from ..permissions import EventPermission
from ..serializers import EventSerializer


class EventViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "code"
    permission_classes = (EventPermission,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.prefetch_related(
            "days", "topics", "tracks", "fees", "papers", "sessions__topics", "venues__rooms",
        )
        return super().retrieve(request, *args, **kwargs)

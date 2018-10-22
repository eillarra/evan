from django.views.decorators.cache import never_cache
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from toucon.models import Conference
from ..permissions import ConferencePermission
from ..serializers import ConferenceSerializer


class ConferenceViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = 'code'
    permission_classes = (ConferencePermission,)
    queryset = Conference.objects.all()
    serializer_class = ConferenceSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.prefetch_related('days', 'sessions__topics', 'topics', 'tracks', 'venues__rooms')
        return super().retrieve(request, *args, **kwargs)

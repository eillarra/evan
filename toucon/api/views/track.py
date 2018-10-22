from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from toucon.models import Track
from ..permissions import ConferenceRelatedObjectPermission
from ..serializers import TrackSerializer
from ..viewsets import ConferenceRelatedCreateOnlyViewSet


class TracksViewSet(ConferenceRelatedCreateOnlyViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer


class TrackViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (ConferenceRelatedObjectPermission,)
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

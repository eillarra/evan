from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Track
from ..permissions import EventRelatedObjectPermission
from ..serializers import TrackSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet


class TracksViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer


class TrackViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

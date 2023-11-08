from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models.tracks import Track

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import TrackSerializer
from ..viewsets import EventRelatedViewSet
from .base import ProtectedMixin


class TracksPermission(EventRelatedPermission):
    allow_list_to_all = False
    allow_create_to_manager = True


class TrackPermission(EventRelatedObjectPermission):
    allow_update_to_manager = True
    allow_delete_to_manager = True


class TracksViewSet(EventRelatedViewSet):
    permission_classes = [TracksPermission]
    queryset = Track.objects.order_by("name").all()
    serializer_class = TrackSerializer


class TrackViewSet(ProtectedMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [TrackPermission]
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Sponsor

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import SponsorSerializer
from ..viewsets import EventRelatedViewSet
from .base import ProtectedMixin


class SponsorsPermission(EventRelatedPermission):
    allow_list_to_all = False
    allow_create_to_manager = True


class SponsorPermission(EventRelatedObjectPermission):
    allow_update_to_manager = True
    allow_delete_to_manager = True


class SponsorsViewSet(EventRelatedViewSet):
    permission_classes = [SponsorsPermission]
    queryset = Sponsor.objects.prefetch_related("files").all()
    pagination_class = None
    serializer_class = SponsorSerializer


class SponsorViewSet(ProtectedMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [SponsorPermission]
    queryset = Sponsor.objects.prefetch_related("files").all()
    serializer_class = SponsorSerializer

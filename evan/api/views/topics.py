from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models.topics import Topic

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import TopicSerializer
from ..viewsets import EventRelatedViewSet
from .base import ProtectedMixin


class TopicsPermission(EventRelatedPermission):
    allow_list_to_all = False
    allow_create_to_manager = True


class TopicPermission(EventRelatedObjectPermission):
    allow_update_to_manager = True
    allow_delete_to_manager = True


class TopicsViewSet(EventRelatedViewSet):
    permission_classes = [TopicsPermission]
    queryset = Topic.objects.order_by("name").all()
    serializer_class = TopicSerializer


class TopicViewSet(ProtectedMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [TopicPermission]
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

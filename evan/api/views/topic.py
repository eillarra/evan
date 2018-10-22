from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Topic
from ..permissions import EventRelatedObjectPermission
from ..serializers import TopicSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet


class TopicsViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class TopicViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

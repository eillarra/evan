from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from toucon.models import Topic
from ..permissions import ConferenceRelatedObjectPermission
from ..serializers import TopicSerializer
from ..viewsets import ConferenceRelatedCreateOnlyViewSet


class TopicsViewSet(ConferenceRelatedCreateOnlyViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class TopicViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (ConferenceRelatedObjectPermission,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

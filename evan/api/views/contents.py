from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Content
from ..permissions import ContentPermission
from ..serializers import ContentSerializer
from ..viewsets import EventRelatedListOnlyViewSet


class ContentsViewSet(EventRelatedListOnlyViewSet):
    queryset = Content.objects.prefetch_related("images").all()
    pagination_class = None
    serializer_class = ContentSerializer


class ContentViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = (ContentPermission,)
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

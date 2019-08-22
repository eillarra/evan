from rest_framework.permissions import AllowAny

from evan.models import Content
from ..serializers import ContentSerializer
from ..viewsets import EventRelatedListOnlyViewSet


class ContentsViewSet(EventRelatedListOnlyViewSet):
    queryset = Content.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = ContentSerializer

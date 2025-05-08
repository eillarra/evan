from ...serializers.rel.remarks import RemarkSerializer
from .base import RelModelViewSet


class RemarkViewSet(RelModelViewSet):
    auto_created_by = True
    pagination_class = None
    serializer_class = RemarkSerializer

    def get_queryset(self):
        return self.get_content_object().remarks.select_related("created_by")  # type: ignore

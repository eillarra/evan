from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import EmailLog

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers.emails import EmailListSerializer, EmailSerializer
from ..viewsets import EventRelatedViewSet


class EmailsPermission(EventRelatedPermission):
    allow_create_to_manager = False


class EmailPermission(EventRelatedObjectPermission):
    allow_update_to_manager = False
    allow_delete_to_manager = False


class EmailsViewSet(EventRelatedViewSet):
    queryset = EmailLog.objects.defer("body")
    pagination_class = None
    permission_classes = [EmailsPermission]
    serializer_class = EmailListSerializer


class EmailViewSet(RetrieveModelMixin, GenericViewSet):
    permission_classes = [EmailPermission]
    queryset = EmailLog.objects.all()
    serializer_class = EmailSerializer

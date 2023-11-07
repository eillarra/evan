from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import File, Session

from ..permissions import SessionPermission
from ..serializers import SessionSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet
from .mixins import FileUploadMixin


class SessionsViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


class SessionViewSet(FileUploadMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (SessionPermission,)
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    max_files = 30
    default_file_type = File.PRIVATE

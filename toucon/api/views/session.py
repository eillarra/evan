from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from toucon.models import Session
from ..permissions import SessionPermission
from ..serializers import SessionSerializer
from ..viewsets import ConferenceRelatedCreateOnlyViewSet


class SessionsViewSet(ConferenceRelatedCreateOnlyViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


class SessionViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (SessionPermission,)
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Keynote

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers.keynotes import KeynoteSerializer, KeynoteWithSecretsSerializer
from ..utils import user_is_manager_of_event
from ..viewsets import EventRelatedViewSet


class KeynotesPermission(EventRelatedPermission):
    allow_list_to_all = True
    allow_retrieve_to_all = True
    allow_create_to_manager = True


class KeynotePermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = True
    allow_update_to_manager = True
    allow_delete_to_manager = True


class KeynotesViewSet(EventRelatedViewSet):
    permission_classes = [KeynotesPermission]
    queryset = Keynote.objects.select_related("event", "session", "subsession").prefetch_related("topics", "files")
    serializer_class = KeynoteSerializer
    filterset_fields = ["session", "subsession", "topics"]
    search_fields = ["code", "title", "speaker", "bio", "abstract"]
    ordering_fields = ["code", "title", "speaker", "created_at"]
    ordering = ["code"]

    def get_serializer_class(self):
        """Event managers can see the UUID and secret."""
        if user_is_manager_of_event(self.request.user, self.get_event()):
            return KeynoteWithSecretsSerializer
        return super().get_serializer_class()


class KeynoteViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Keynote.objects.select_related("event", "session", "subsession").prefetch_related("topics", "files")
    serializer_class = KeynoteSerializer
    permission_classes = [KeynotePermission]

    def get_serializer_class(self):
        """Event managers can see the UUID and secret."""
        if user_is_manager_of_event(self.request.user, self.get_object().event):
            return KeynoteWithSecretsSerializer
        return super().get_serializer_class()

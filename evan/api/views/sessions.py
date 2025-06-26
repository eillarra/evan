from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Session

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import SessionSerializer, SessionWithSecretsSerializer
from ..utils import user_is_manager_of_event
from ..viewsets import EventRelatedViewSet


class SessionsPermission(EventRelatedPermission):
    allow_list_to_all = True
    allow_retrieve_to_all = True
    allow_create_to_manager = True


class SessionPermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = True
    allow_update_to_manager = True
    allow_delete_to_manager = True

    def has_object_permission(self, request, view, obj):
        # some users can send an X-Evan-Secret header that allows them to edit the session
        if (
            request.method in ["PUT", "PATCH"]
            and "HTTP_X_EVAN_SECRET" in request.META
            and request.META["HTTP_X_EVAN_SECRET"] == obj.secret
        ):
            return True

        return super().has_object_permission(request, view, obj)


class SessionsViewSet(EventRelatedViewSet):
    permission_classes = [SessionsPermission]
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()
        return queryset.prefetch_related("files", "topics", "subsessions", "track", "room")

    def get_serializer_class(self):
        """Use appropriate serializer based on action and permissions."""
        if user_is_manager_of_event(self.request.user, self.get_event()):
            return SessionWithSecretsSerializer
        return super().get_serializer_class()


class SessionViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [SessionPermission]
    queryset = Session.objects.prefetch_related("files", "topics").all()
    serializer_class = SessionSerializer

    def get_serializer_class(self):
        """Event managers can see the UUID and secret."""
        if user_is_manager_of_event(self.request.user, self.get_object().event):
            return SessionWithSecretsSerializer
        return super().get_serializer_class()

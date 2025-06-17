from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import File, Paper

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import PaperSerializer, PaperWithSecretsSerializer
from ..utils import user_is_manager_of_event
from ..viewsets import EventRelatedViewSet


class PapersPermission(EventRelatedPermission):
    allow_list_to_all = True
    allow_retrieve_to_all = True
    allow_create_to_manager = True


class PaperPermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = True
    allow_update_to_manager = True
    allow_delete_to_manager = True

    def has_object_permission(self, request, view, obj):
        # some users can send an X-Evan-Secret header that allows them to edit the paper
        if (
            request.method in ["PUT", "PATCH"]
            and "HTTP_X_EVAN_SECRET" in request.META
            and request.META["HTTP_X_EVAN_SECRET"] == obj.secret
        ):
            return True

        return super().has_object_permission(request, view, obj)


class PapersViewSet(EventRelatedViewSet):
    permission_classes = [PapersPermission]
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer

    def get_serializer_class(self):
        """Event managers can see the UUID and secret."""
        if user_is_manager_of_event(self.request.user, self.get_event()):
            return PaperWithSecretsSerializer
        return super().get_serializer_class()


class PaperViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [PaperPermission]
    queryset = Paper.objects.all()
    serializer_class = PaperSerializer
    max_files = 30
    default_file_type = File.PRIVATE

    def get_serializer_class(self):
        """Event managers can see the UUID and secret."""
        if user_is_manager_of_event(self.request.user, self.get_object().event):
            return PaperWithSecretsSerializer
        return super().get_serializer_class()

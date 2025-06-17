from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, File, Session, Subsession

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import SubsessionSerializer, SubsessionWithSecretsSerializer
from ..utils import user_is_manager_of_event


class SubsessionsPermission(EventRelatedPermission):
    allow_list_to_all = True
    allow_retrieve_to_all = True
    allow_create_to_manager = True

    def get_event(self, view) -> Event:
        if not self._event:
            try:
                session_id = view.kwargs.get("parent_lookup_session_id")
                session = Session.objects.get(pk=session_id)
                self._event = session.event
            except Session.DoesNotExist as exc:
                from rest_framework.exceptions import NotFound

                raise NotFound("Session does not exist.") from exc
        return self._event


class SubsessionPermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = True
    allow_update_to_manager = True
    allow_delete_to_manager = True

    def get_event(self, obj):
        if not self._event:
            try:
                self._event = obj.session.event
            except Exception as exc:
                from rest_framework.exceptions import NotFound

                raise NotFound("Event does not exist.") from exc
        return self._event

    def has_object_permission(self, request, view, obj):
        if (
            request.method in ["PUT", "PATCH"]
            and "HTTP_X_EVAN_SECRET" in request.META
            and request.META["HTTP_X_EVAN_SECRET"] == obj.secret
        ):
            return True

        return super().has_object_permission(request, view, obj)


class SubsessionsViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    permission_classes = [SubsessionsPermission]
    queryset = Subsession.objects.all()
    serializer_class = SubsessionSerializer

    def get_queryset(self):
        session_id = self.kwargs.get("parent_lookup_session_id")
        return self.queryset.filter(session_id=session_id)

    def get_serializer_class(self):
        session_id = self.kwargs.get("parent_lookup_session_id")
        try:
            session = Session.objects.get(pk=session_id)
            if user_is_manager_of_event(self.request.user, session.event):
                return SubsessionWithSecretsSerializer
        except Session.DoesNotExist:
            pass
        return super().get_serializer_class()

    def perform_create(self, serializer):
        session_id = self.kwargs.get("parent_lookup_session_id")
        try:
            session = Session.objects.get(pk=session_id)
            serializer.save(session=session)
        except Session.DoesNotExist as exc:
            from rest_framework.exceptions import NotFound

            raise NotFound("Session not found.") from exc


class SubsessionViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [SubsessionPermission]
    queryset = Subsession.objects.all()
    serializer_class = SubsessionSerializer
    max_files = 30
    default_file_type = File.PRIVATE

    def get_serializer_class(self):
        if user_is_manager_of_event(self.request.user, self.get_object().session.event):
            return SubsessionWithSecretsSerializer
        return super().get_serializer_class()

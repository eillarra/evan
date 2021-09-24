from django.db import IntegrityError
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Abstract, File
from ..permissions import AbstractPermission
from ..serializers import AbstractRetrieveSerializer
from ..viewsets import EventRelatedViewSet


class AbstractsViewSet(EventRelatedViewSet):
    queryset = Abstract.objects.prefetch_related("files")
    serializer_class = AbstractRetrieveSerializer

    def list(self, request, *args, **kwargs):
        self.serializer_class = AbstractRetrieveSerializer
        return super().list(request, *args, **kwargs)


class AbstractCreateViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Abstract.objects.select_related("user__profile")
    serializer_class = AbstractRetrieveSerializer

    def perform_create(self, serializer):
        try:
            serializer.save(
                user=self.request.user,
                event=Event.objects.get(code=self.kwargs.get("code")),
            )
        except IntegrityError:
            raise ValidationError({"event-user": ["Duplicate entry - this user already has an abstract."]})


class AbstractViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "uuid"
    permission_classes = (AbstractPermission,)
    queryset = Abstract.objects.select_related("user__profile")
    serializer_class = AbstractRetrieveSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        serializer_class=AbstractRetrieveSerializer,
        parser_classes=[FileUploadParser],
    )
    @never_cache
    def files(self, request, *args, **kwargs):
        abstract = self.get_object()

        try:
            max_files = abstract.event.config["abstracts"]["uploader"]["max_files"]
            if abstract.files.count() >= max_files:
                raise ValidationError({"files": [f"You have reached the limit on number of files ({max_files})."]})
        except KeyError:
            raise ValidationError({"files": ["Abstract module is not active."]})

        file = File(content_object=self.get_object(), type=File.PRIVATE, file=request.data["file"])
        file.save()
        return self.retrieve(request, *args, **kwargs)

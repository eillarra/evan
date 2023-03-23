from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Abstract, AbstractReview, File
from ..permissions import AbstractPermission, AbstractReviewPermission
from ..serializers import (
    AbstractSerializer,
    ManagedAbstractSerializer,
    AbstractReviewSerializer,
    FullAbstractReviewSerializer,
)
from ..viewsets import EventRelatedViewSet


class AbstractsViewSet(EventRelatedViewSet):
    queryset = Abstract.objects.select_related("event", "user__profile").prefetch_related("files", "reviews")
    serializer_class = ManagedAbstractSerializer


class AbstractCreateViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Abstract.objects.select_related("user__profile")
    serializer_class = AbstractSerializer

    def perform_create(self, serializer):
        try:
            serializer.save(
                user=self.request.user,
                event=Event.objects.get(code=self.kwargs.get("code")),
            )
        except IntegrityError:
            raise ValidationError({"event-user": ["Duplicate entry - this user already has an abstract."]})


class AbstractViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """
    This viewset is used for retrieving and updating abstracts and is open to all users.
    """

    lookup_field = "uuid"
    permission_classes = (AbstractPermission,)
    queryset = Abstract.objects.select_related("event", "user__profile").prefetch_related("files", "reviews")
    serializer_class = AbstractSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            abstract = self.get_object()
            if abstract.user != self.request.user and abstract.event.can_be_managed_by(self.request.user):
                return ManagedAbstractSerializer
        return super().get_serializer_class()

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        serializer_class=AbstractSerializer,
        parser_classes=[FileUploadParser],
    )
    @method_decorator(never_cache)
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


class AbstractReviewsViewSet(ListModelMixin, GenericViewSet):
    pagination_class = None
    queryset = AbstractReview.objects.prefetch_related("abstract__files", "abstract__user__profile")
    serializer_class = FullAbstractReviewSerializer

    @method_decorator(never_cache)
    def list(self, request, *args, **kwargs):
        event_id = Event.objects.values_list("id", flat=True).get(code=self.kwargs.get("code"))
        self.queryset = self.queryset.filter(abstract__event_id=event_id, user_id=request.user.id)
        return super().list(request, *args, **kwargs)


class AbstractReviewCreateViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = AbstractReview.objects.select_related("abstract__event", "user")
    serializer_class = AbstractReviewSerializer

    def perform_create(self, serializer):
        event = Event.objects.get(code=self.kwargs.get("code"))

        if not event.can_be_managed_by(self.request.user):
            raise PermissionDenied("Only managers can create a new review.")

        super().perform_create(serializer)


class AbstractReviewViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    lookup_field = "id"
    permission_classes = (AbstractReviewPermission,)
    queryset = AbstractReview.objects.select_related("abstract__event", "user")
    serializer_class = AbstractReviewSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

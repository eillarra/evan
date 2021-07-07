from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import FileUploadParser
from rest_framework.viewsets import GenericViewSet

from evan.models import Sponsor, File
from ..permissions import EventRelatedObjectPermission
from ..serializers import SponsorSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet


class SponsorsViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Sponsor.objects.prefetch_related("files").all()
    pagination_class = None
    serializer_class = SponsorSerializer


class SponsorViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Sponsor.objects.prefetch_related("files").all()
    serializer_class = SponsorSerializer

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        serializer_class=SponsorSerializer,
        parser_classes=[FileUploadParser],
    )
    @never_cache
    def files(self, request, *args, **kwargs):
        sponsor = self.get_object()

        if sponsor.files.count() > 1:
            raise ValidationError({"files": ["You have reached the limit on number of files (1)."]})

        file = File(content_object=sponsor, type=File.PUBLIC, file=request.data["file"])
        file.save()
        return RetrieveModelMixin.retrieve(self, request, *args, **kwargs)

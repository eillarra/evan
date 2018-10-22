from django.views.decorators.cache import never_cache
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.schemas import AutoSchema
from rest_framework.viewsets import GenericViewSet

from toucon.models import Conference
from .permissions import ConferenceRelatedPermission
from .schema import conference_code_field


class ConferenceCreateModelMixin(CreateModelMixin):
    def perform_create(self, serializer):
        serializer.save(conference=Conference.objects.get(code=self.kwargs.get('code')))


class ConferenceListModelMixin(ListModelMixin):
    @never_cache
    def list(self, request, *args, **kwargs):
        conference_id = Conference.objects.values_list('id', flat=True).get(code=self.kwargs.get('code'))
        self.queryset = self.queryset.filter(conference_id=conference_id)
        return super().list(request, *args, **kwargs)


class ConferenceRelatedViewSet(ConferenceListModelMixin, ConferenceCreateModelMixin, GenericViewSet):
    permission_classes = (ConferenceRelatedPermission,)
    pagination_class = None
    schema = AutoSchema(manual_fields=[conference_code_field])


class ConferenceRelatedCreateOnlyViewSet(ConferenceCreateModelMixin, GenericViewSet):
    permission_classes = (ConferenceRelatedPermission,)
    schema = AutoSchema(manual_fields=[conference_code_field])

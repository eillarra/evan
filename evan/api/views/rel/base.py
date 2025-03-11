from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.viewsets import ModelViewSet

from ..base import ProtectedMixin


class RelModelViewSet(ProtectedMixin, ModelViewSet):
    _content_object = None
    auto_created_by = False

    def get_content_object(self):
        if self._content_object:
            return self._content_object

        # get ContentType content object based on the URL parameters
        content_type_id = self.kwargs.get("parent_lookup_content_type_id")
        object_id = self.kwargs.get("parent_lookup_object_id")
        self._content_object = ContentType.objects.get(id=content_type_id).get_object_for_this_type(id=object_id)
        return self._content_object

    def perform_create(self, serializer):
        if self.auto_created_by:
            serializer.save(content_object=self.get_content_object(), created_by=self.request.user)
        else:
            serializer.save(content_object=self.get_content_object())

    def perform_update(self, serializer):
        if self.auto_created_by:
            serializer.save(content_object=self.get_content_object(), updated_by=self.request.user)
        else:
            serializer.save(content_object=self.get_content_object())

    @method_decorator(never_cache)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

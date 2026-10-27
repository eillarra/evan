from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.viewsets import ModelViewSet

from ..base import ProtectedMixin


class RelModelViewSet(ProtectedMixin, ModelViewSet):
    _content_object = None
    auto_created_by = False

    def get_content_object(self):
        """Return the object the related collection belongs to.

        :returns: The content object named by the URL.
        :raises Http404: If the content type or the object does not exist.
        """
        if self._content_object:
            return self._content_object

        # get ContentType content object based on the URL parameters
        content_type = get_object_or_404(ContentType, id=self.kwargs.get("parent_lookup_content_type_id"))
        model = content_type.model_class()
        if model is None:
            raise Http404

        try:
            self._content_object = get_object_or_404(model, pk=self.kwargs.get("parent_lookup_object_id"))
        except ValueError as exc:
            # The nested route accepts any object id, not only a number.
            raise Http404 from exc

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

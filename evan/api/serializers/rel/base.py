from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from ..base import NestedHyperlinkField


class RelHyperlinkedField(serializers.HyperlinkedIdentityField):
    """Hyperlinked field for related objects."""

    def get_url(self, obj, view_name, request, format):
        """Get URL for related object."""
        ct = ContentType.objects.get_for_model(obj)
        self.view_name = view_name
        return self.reverse(
            self.view_name,
            kwargs={"parent_lookup_content_type_id": ct.id, "parent_lookup_object_id": obj.pk},
            request=request,
            format=format,
        )


class NestedRelHyperlinkField(NestedHyperlinkField):
    """Specific nested field for ContentType objects."""

    def __init__(self, view_name: str, **kwargs):
        nested_lookup = {
            "parent_lookup_content_type_id": "content_type_id",
            "parent_lookup_object_id": "object_id",
        }
        super().__init__(view_name, nested_lookup, **kwargs)

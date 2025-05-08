from rest_framework import serializers

from evan.models.rel.remarks import Remark

from ..base import TagsMixin
from ..users import UserTinySerializer
from .base import NestedRelHyperlinkField, RelHyperlinkedField


class RemarkSerializer(TagsMixin, serializers.ModelSerializer):
    """Remark serializer."""

    self = NestedRelHyperlinkField(view_name="v1:remark-detail")
    created_by = UserTinySerializer(read_only=True)

    class Meta:  # noqa: D106
        model = Remark
        fields = ["id", "self", "text", "created_at", "created_by"]


class RemarksMixin(serializers.ModelSerializer):
    """Remarks mixin."""

    rel_remarks = RelHyperlinkedField(view_name="v1:remark-list")

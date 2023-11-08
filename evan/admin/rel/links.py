from django.contrib.contenttypes.admin import GenericTabularInline

from evan.models.rel.links import Link


class LinksInline(GenericTabularInline):
    """Reusable inline for Link model."""

    model = Link
    classes = ("collapse",)
    extra = 0

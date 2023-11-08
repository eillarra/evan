from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Link(models.Model):
    """Online accounts and other links."""

    WEBSITE = "website"
    LINKEDIN = "linkedin"
    OTHER = "other"
    TYPES = (
        (WEBSITE, "Website"),
        (LINKEDIN, "LinkedIn"),
        (OTHER, "Other"),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="links")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    type = models.CharField(max_length=16, choices=TYPES, default=WEBSITE)
    url = models.URLField()

    class Meta:  # noqa: D106
        db_table = "evan_rel_link"

    def __str__(self) -> str:
        return self.url


class LinksMixin(models.Model):
    links = GenericRelation(Link)

    class Meta:  # noqa: D106
        abstract = True

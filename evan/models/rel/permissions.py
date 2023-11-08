from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Permission(models.Model):
    """
    Event auth model.
    Higher permission levels inherit lower permissions, simplifying queries.
    """

    OWNER = 9
    ADMIN = 5
    GUEST = 1
    LEVEL_CHOICES = (
        (OWNER, "Owner"),
        (ADMIN, "Administrator"),
        (GUEST, "Guest"),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="perms")
    object_id = models.IntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    user = models.ForeignKey("evan.User", blank=True, related_name="perms", on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(db_index=True, choices=LEVEL_CHOICES)

    class Meta:  # noqa: D106
        db_table = "evan_rel_permission"
        ordering = ["content_type", "object_id", "-level"]
        unique_together = ["content_type", "object_id", "user"]

    def __str__(self) -> str:
        return f"{self.object_id} ({self.level})"


class PermissionsMixin(models.Model):
    """A mixin for models that need permissions."""

    acl = GenericRelation(Permission)

    class Meta:  # noqa: D106
        abstract = True

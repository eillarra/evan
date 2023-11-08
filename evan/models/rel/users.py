from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property


class RelatedUser(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="rel_users")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    user = models.ForeignKey("evan.User", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "evan_rel_user"
        ordering = ["content_type", "object_id"]
        unique_together = ["content_type", "object_id", "user"]

    def __str__(self) -> str:
        return f"{self.pk} ({self.user})"


class UsersMixin(models.Model):
    rel_users = GenericRelation(RelatedUser)

    class Meta:
        abstract = True

    @cached_property
    def users(self) -> list:
        return [rel.user for rel in self.rel_users.all()]

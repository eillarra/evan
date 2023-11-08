from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Remark(models.Model):
    """Remarks made by administrators."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="remarks")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    text = models.TextField()

    class Meta:  # noqa: D106
        db_table = "evan_rel_remark"

    def __str__(self) -> str:
        return f"Remark: {self.pk}"


class RemarksMixin(models.Model):
    """Mixin for models that can have remarks."""

    remarks = GenericRelation(Remark)

    class Meta:  # noqa: D106
        abstract = True

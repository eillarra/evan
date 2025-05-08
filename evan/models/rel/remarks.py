from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


def append_remarks_tags(obj, *, tags: list[str]) -> list[str]:
    """For an object, process the tags."""
    tags = [tag for tag in tags if not tag.startswith("remarks.")]
    tags.append(f"remarks.count:{obj.remarks.count()}")
    return tags


class Remark(models.Model):
    """Remarks made by administrators."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="remarks")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "evan.User", related_name="remarks_created", on_delete=models.SET_NULL, null=True, blank=True, editable=False
    )

    class Meta:  # noqa: D106
        db_table = "evan_rel_remark"

    def __str__(self) -> str:
        return f"Remark: {self.pk}"


class RemarksMixin(models.Model):
    """Mixin for models that can have remarks."""

    remarks = GenericRelation(Remark)

    class Meta:  # noqa: D106
        abstract = True


@receiver(post_save, sender=Remark)
def post_save_remark(sender, instance, **kwargs):
    """Update the remark tags of the associated object when an evaluation is saved."""
    sync_remark_tags(instance)


@receiver(post_delete, sender=Remark)
def post_delete_remark(sender, instance, **kwargs):
    """Update the remark tags of the associated object when an evaluation is deleted."""
    sync_remark_tags(instance)


def sync_remark_tags(instance):
    """Sync the remark tags of the associated object."""
    from evan.models import Registration

    for Model in {Registration}:
        if isinstance(instance.content_object, Model):
            Model.update_tags(instance.content_object, type="remarks")
            break

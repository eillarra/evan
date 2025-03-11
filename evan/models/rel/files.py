from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from evan.services.file_guard import check_file_access
from evan.services.s3 import delete_s3_object

from ..validators import validate_list_of_strings


if TYPE_CHECKING:
    from evan.models.users import User


def get_upload_path(instance, filename) -> str:
    """Get the upload path for a file."""
    return f"{instance.type}/{instance.content_type_id}/{instance.object_id}/{filename}".lower()


class File(models.Model):
    """A file attached to a model."""

    PUBLIC = "public"
    PRIVATE = "private"
    TYPE_CHOICES = (
        (PUBLIC, "Public"),
        (PRIVATE, "Private"),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="files")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    type = models.CharField(max_length=8, choices=TYPE_CHOICES)
    file = models.FileField(upload_to=get_upload_path)
    description = models.CharField(max_length=255, blank=True, default="")
    tags = models.JSONField(default=list, validators=[validate_list_of_strings])

    class Meta:  # noqa: D106
        db_table = "evan_rel_file"
        indexes = [
            models.Index(fields=["file"]),
        ]
        ordering = ["content_type", "object_id"]

    def __str__(self) -> str:
        return self.file.name

    def delete(self, *args, **kwargs):
        """Delete the file from S3 before deleting the model."""
        try:
            delete_s3_object(self.s3_object_key)
        except Exception:
            pass
        super().delete(*args, **kwargs)

    def is_accessible_by_user(self, user: "User") -> bool:
        """Check if the file is accessible by a user."""
        if self.file.name.startswith("public/"):
            return True
        return check_file_access(self, user)

    @property
    def s3_object_key(self):
        return self.file.name

    @property
    def url(self):
        """The URL to the file."""
        return reverse("media_file", args=[self.file.name])


class FilesMixin(models.Model):
    """A mixin to add files to a model."""

    files = GenericRelation(File)

    class Meta:  # noqa: D106
        abstract = True

    def files_can_be_managed_by(self, user: "User") -> bool:
        """Check if the user can manage related files."""
        raise NotImplementedError("files_can_be_managed_by must be implemented in the model using this mixin.")

import base64
import os
import secrets
from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

from evan.services.file_guard import check_file_access
from evan.services.s3 import delete_s3_object

from ..validators import validate_list_of_strings


if TYPE_CHECKING:
    from evan.models.users import User


def get_upload_path(instance, filename) -> str:
    """Get the upload path for a file.

    Generates a unique, collision-free path using the instance's type, content type,
    object ID, and a slugified filename with URL-safe unique identifier.

    :param instance: The File model instance being saved.
    :param filename: The original filename uploaded by the user.
    :returns: A safe, unique file path for storage.
    """
    unique_id = base64.urlsafe_b64encode(secrets.token_bytes(6)).decode("utf-8").rstrip("=")
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)[:50]
    if not clean_name:  # Fallback for empty or non-ASCII filenames
        clean_name = "file"
    clean_ext = ext.lower() if ext else ""
    new_filename = f"{clean_name}_{unique_id}{clean_ext}"
    return f"{instance.type}/{instance.content_type_id}/{instance.object_id}/{new_filename}"


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

    def is_accessible_by_user(self, user: User) -> bool:
        """Check if the file is accessible by a user."""
        if self.is_public:
            return True
        return check_file_access(self, user)

    @property
    def is_public(self) -> bool:
        """Check if the file is public."""
        return self.type == self.PUBLIC

    @property
    def s3_object_key(self):
        return self.file.name


class FilesMixin(models.Model):
    """A mixin to add files to a model."""

    files = GenericRelation(File)

    class Meta:  # noqa: D106
        abstract = True

    def files_can_be_managed_by(self, user: User) -> bool:
        """Check if the user can manage related files."""
        if hasattr(self, "event") and self.event:  # type: ignore
            return self.event.can_be_managed_by(user)  # type: ignore
        elif hasattr(self, "can_be_managed_by"):
            return self.can_be_managed_by(user)  # type: ignore
        raise NotImplementedError("files_can_be_managed_by must be implemented in the model using this mixin.")

    def files_viewable_by_user(self, user: User) -> bool:
        """Check if the user can view related files.

        Default: managers of the related event, or accepted attendees
        registered for it. Override for custom behaviour (e.g. Album excludes
        no-shows, Abstract allows authors and reviewers).

        :param user: The user to check access for.
        :returns: True if the user can view the related files.
        :raises NotImplementedError: If no access control can be determined.
        """
        if hasattr(self, "event") and self.event:  # type: ignore
            event = self.event
            return (
                event.can_be_managed_by(user) or event.registrations.filter(user_id=user.id, is_accepted=True).exists()
            )
        elif hasattr(self, "can_be_managed_by"):
            return self.can_be_managed_by(user)  # type: ignore
        raise NotImplementedError("files_viewable_by_user must be implemented in the model using this mixin.")

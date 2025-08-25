from typing import TYPE_CHECKING

from django.db import models

from .rel.files import FilesMixin


if TYPE_CHECKING:
    from evan.models.users import User


class Album(FilesMixin, models.Model):
    """A photo album for an event."""

    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="albums")
    title = models.CharField(max_length=200)

    class Meta:  # noqa: D106
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.event.code} - {self.title}"

    def files_can_be_managed_by(self, user: "User") -> bool:
        """Check if the user can manage album files."""
        return self.event.can_be_managed_by(user)

    def is_accessible_by_user(self, user: "User") -> bool:
        """Check if the album is accessible by a user (registered attendees only)."""
        if self.event.can_be_managed_by(user):
            return True

        # Check if user is a registered attendee (not no-show)
        return self.event.registrations.filter(
            user_id=user.id,  # type: ignore
            is_accepted=True,
            no_show=False,
        ).exists()

    def get_original_photos(self):
        """Get all original photos in the album."""
        # Use icontains for SQLite compatibility in tests
        from django.db import connection

        if connection.vendor == "sqlite":
            return self.files.filter(tags__icontains="gallery:original")
        return self.files.filter(tags__contains=["gallery:original"])

    def get_thumbnail_photos(self):
        """Get all thumbnail photos in the album."""
        # Use icontains for SQLite compatibility in tests
        from django.db import connection

        if connection.vendor == "sqlite":
            return self.files.filter(tags__icontains="gallery:thumbnail")
        return self.files.filter(tags__contains=["gallery:thumbnail"])

    def get_photo_pairs(self):
        """Get all photo pairs (original + thumbnail) in the album."""
        originals = self.get_original_photos()
        pairs = []

        for original in originals:
            # Find the thumbnail ID from the original's tags
            thumbnail_id = None
            for tag in original.tags:
                if tag.startswith("thumbnail_id:"):
                    thumbnail_id = tag.split(":", 1)[1]
                    break

            thumbnail = None
            if thumbnail_id:
                try:
                    thumbnail = self.files.get(id=thumbnail_id)
                except self.files.model.DoesNotExist:  # type: ignore
                    pass

            pairs.append(
                {
                    "original": original,
                    "thumbnail": thumbnail,
                }
            )

        return pairs

    def get_collection_zip(self):
        """Get the collection zip file for the album.

        :returns: The zip File object or None if it doesn't exist.
        """
        # Use icontains for SQLite compatibility in tests
        from django.db import connection

        if connection.vendor == "sqlite":
            return self.files.filter(tags__icontains="gallery:collection").first()
        return self.files.filter(tags__contains=["gallery:collection"]).first()

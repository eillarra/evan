from django.db import models

from .rel.files import FilesMixin


class Sponsor(FilesMixin, models.Model):
    """A sponsor for an event."""

    event = models.ForeignKey("evan.Event", related_name="sponsors", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    website = models.URLField()
    level = models.PositiveSmallIntegerField(default=0)

    class Meta:  # noqa: D106
        ordering = ["event", "level", "name"]

    def __str__(self) -> str:
        return self.name

    def editable_by_user(self, user) -> bool:
        return self.event.editable_by_user(user)

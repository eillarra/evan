from django.contrib.contenttypes.fields import GenericRelation
from django.db import models


class Sponsor(models.Model):
    """A sponsor for an event."""

    event = models.ForeignKey("evan.Event", related_name="sponsors", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    website = models.URLField()
    level = models.PositiveSmallIntegerField(default=0)
    files = GenericRelation("evan.File")

    class Meta:  # noqa: D106
        ordering = ["event", "level", "name"]

    def __str__(self) -> str:
        return self.name

    def editable_by_user(self, user) -> bool:
        return self.event.editable_by_user(user)

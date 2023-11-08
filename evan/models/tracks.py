from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Track(models.Model):
    """A track for an event."""

    event = models.ForeignKey("evan.Event", related_name="tracks", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:  # noqa: D106
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def get_api_url(self) -> str:
        return reverse("v1:track-detail", args=[self.pk])

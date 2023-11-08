from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Topic(models.Model):
    """A topic for an event."""

    event = models.ForeignKey("evan.Event", related_name="topics", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    class Meta:  # noqa: D106
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def get_api_url(self) -> str:
        return reverse("v1:topic-detail", args=[self.pk])

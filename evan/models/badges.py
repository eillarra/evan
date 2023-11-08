from django.db import models
from django_countries.fields import CountryField


class Badge(models.Model):
    """Extra badge for non-registered event attendee."""

    event = models.ForeignKey("evan.Event", on_delete=models.CASCADE, related_name="extra_badges")
    name = models.CharField(max_length=190, default="", blank=True)
    affiliation = models.CharField(max_length=190, default="", blank=True)
    country = CountryField()
    custom_color = models.CharField(max_length=7, default="", blank=True)

    class Meta:  # noqa: D106
        ordering = ["event", "name"]

    def __str__(self) -> str:
        return self.name

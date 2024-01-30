from django.db import models
from django_countries.fields import CountryField


class Badge(models.Model):
    """
    Extra badges that can be manualkly added to the event.
    """

    event = models.ForeignKey("evan.Event", on_delete=models.CASCADE, related_name="extra_badges")
    name = models.CharField(max_length=190, null=True, blank=True)
    affiliation = models.CharField(max_length=190, null=True, blank=True)
    country = CountryField()
    custom_color = models.CharField(max_length=7, null=True, blank=True)

    class Meta:
        ordering = ("event", "name")

    def __str__(self) -> str:
        return self.name

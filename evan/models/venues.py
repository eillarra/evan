from django.db import models
from django.urls import reverse


class Venue(models.Model):
    event = models.ForeignKey("evan.Event", related_name="venues", on_delete=models.CASCADE)
    is_main = models.BooleanField(default=False)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=160, default="", blank=True)
    presentation = models.TextField(default="", blank=True)
    website = models.URLField(max_length=200, default="", blank=True)
    google_place_id = models.CharField(
        max_length=200, default="", blank=True, help_text="Google Places API place ID for enhanced location features"
    )

    class Meta:  # noqa: D106
        ordering = ["event", "-is_main", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.event.country})"

    def save(self, *args, **kwargs) -> None:
        """Save the venue with main venue constraint enforcement.

        If this venue is being set as main, all other venues for the same event
        will have their is_main status set to False.
        """
        self.city = self.event.city if not self.city else self.city

        # If this venue is being set as main, ensure no other venue for this event is main
        if self.is_main:
            Venue.objects.filter(event=self.event, is_main=True).exclude(pk=self.pk).update(is_main=False)

        super().save(*args, **kwargs)

    def get_api_url(self) -> str:
        """Return the API URL for this venue."""
        return reverse("v1:venue-detail", args=[self.pk])


class Room(models.Model):
    venue = models.ForeignKey("evan.Venue", related_name="rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    max_capacity = models.PositiveSmallIntegerField(default=0)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:  # noqa: D106
        db_table = "evan_venue_room"
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.venue} - Room: {self.name}"

    def get_api_url(self) -> str:
        """Return the API URL for this room."""
        return reverse("v1:room-detail", args=[self.pk])

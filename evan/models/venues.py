from django.db import models

from evan.services.geocoding import geocode


class Venue(models.Model):
    event = models.ForeignKey("evan.Event", related_name="venues", on_delete=models.CASCADE)
    is_main = models.BooleanField(default=False)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=160, null=True, blank=True)
    presentation = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=160, null=True, blank=True)
    lat = models.FloatField("Latitude", blank=True, null=True)
    lng = models.FloatField("Longitude", blank=True, null=True)
    website = models.URLField(null=True, blank=True)

    def __str__(self) -> str:
        return "{0} ({1}, {2})".format(self.name, self.city, self.event.country)

    def save(self, *args, **kwargs) -> None:
        self.city = self.event.city if not self.city else self.city
        if self.address and self.address != "":
            self.lat, self.lng = geocode(self.full_address)
        super().save(*args, **kwargs)

    @property
    def full_address(self) -> str:
        return "{0}, {1}, {2}".format(self.address, self.city, self.event.country)


class Room(models.Model):
    venue = models.ForeignKey(Venue, related_name="rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    max_capacity = models.PositiveSmallIntegerField(default=0)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("position",)

    def __str__(self) -> str:
        return "{0} - Room: {1}".format(self.venue, self.name)

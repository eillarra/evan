from django.contrib.contenttypes.fields import GenericRelation
from django.db import models


class Content(models.Model):
    """
    Contents are used to manage page contents for dedicated web pages.
    """

    event = models.ForeignKey("evan.Event", related_name="contents", on_delete=models.CASCADE)
    key = models.CharField(max_length=32)
    value = models.TextField(null=True, blank=True)
    marked = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    images = GenericRelation("evan.File")

    class Meta:
        indexes = [
            models.Index(fields=["event", "key"]),
        ]
        unique_together = ("event", "key")
        ordering = ("event", "key")

    def __str__(self) -> str:
        return self.key

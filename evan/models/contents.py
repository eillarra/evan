import os

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Image(models.Model):
    """
    Application images.
    """

    FOLDER = "public/images"

    image = models.FileField("Image", upload_to=FOLDER, null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="images")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["content_type", "object_id", "position"]

    def delete(self, *args, **kwargs):
        if os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


class Content(models.Model):
    """
    Contents are used to manage page contents for dedicated web pages.
    """

    event = models.ForeignKey("evan.Event", related_name="contents", on_delete=models.CASCADE)
    key = models.CharField(max_length=32)
    value = models.TextField(null=True, blank=True)

    notes = models.CharField(max_length=255, blank=True)
    images = GenericRelation("evan.Image")

    class Meta:
        indexes = [
            models.Index(fields=["event", "key"]),
        ]
        unique_together = ("event", "key")
        ordering = ("event", "key")

    def __str__(self) -> str:
        return self.key

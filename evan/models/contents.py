from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from typing import List


class Content(models.Model):
    """
    Contents are used to manage page contents for dedicated web pages.
    """

    event = models.ForeignKey("evan.Event", related_name="contents", on_delete=models.CASCADE)
    key = models.CharField(max_length=32)
    value = models.TextField(null=True, blank=True)
    files = GenericRelation("evan.File")

    config = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["event", "key"]),
        ]
        unique_together = ("event", "key")
        ordering = ("event", "key")

    def __str__(self) -> str:
        return self.key

    def editable_by_user(self, user) -> bool:
        return self.event.editable_by_user(user)

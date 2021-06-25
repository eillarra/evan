import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse


class Abstract(models.Model):
    """
    Paper abstract.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="abstracts", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name="abstracts", on_delete=models.CASCADE)

    title = models.CharField(max_length=512)
    authors = models.CharField(max_length=512)
    abstract = models.TextField()
    files = GenericRelation("evan.File")

    custom_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.uuid} ({self.user})"

    def editable_by_user(self, user) -> bool:
        return self.user_id == user.id

    def viewable_by_user(self, user) -> bool:
        return self.editable_by_user(user) or self.event.editable_by_user(user)

    def get_absolute_url(self) -> str:
        return reverse("abstract:app", args=[self.uuid])

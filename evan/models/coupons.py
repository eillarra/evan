import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Coupon(models.Model):
    """Coupon for an event."""

    code = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="coupons", on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=190, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # noqa: D106
        indexes = [
            models.Index(fields=["code"]),
        ]
        ordering = ["event", "id"]

    def __str__(self) -> str:
        return f"{self.code} ({self.value})"

    def get_api_url(self) -> str:
        return reverse("v1:coupon-detail", args=[self.pk])

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Coupon(models.Model):
    """Coupon for an event."""

    BASE_FEE = "base_fee"
    ALL_FEES = "all_fees"
    COVERAGE_CHOICES = [
        (BASE_FEE, "Base fee"),
        (ALL_FEES, "All fees"),
    ]

    code = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="coupons", on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    coverage = models.CharField(
        max_length=8,
        choices=COVERAGE_CHOICES,
        default=BASE_FEE,
        help_text="What fees are covered by this coupon.",
    )
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

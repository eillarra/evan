from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .base import NonEditableMixin


class Payment(NonEditableMixin, models.Model):
    """A payment transaction for a registration."""

    STRIPE_CHARGE = "stripe_charge"
    STRIPE_REFUND = "stripe_refund"
    TYPE_CHOICES = (
        (STRIPE_CHARGE, "Stripe charge"),
        (STRIPE_REFUND, "Stripe refund"),
    )

    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"
    STATUS_CHOICES = (  # https://stripe.com/docs/api#charge_object-status
        (SUCCEEDED, "Succeeded"),
        (PENDING, "Pending"),
        (FAILED, "Failed"),
    )

    registration = models.ForeignKey("evan.Registration", related_name="payments", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=STRIPE_CHARGE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=FAILED)
    outcome = models.TextField(default="", blank=True)
    stripe_id = models.CharField(max_length=64, default="", blank=True)
    stripe_response = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # noqa: D106
        db_table = "evan_log_payment"

    def __str__(self) -> str:
        return f"{self.registration} ({self.amount}) - {self.type} - {self.status}"


class RegistrationPaymentAttempt(models.Model):
    """Track a single Worldline payment attempt for a registration.

    The attempt is keyed by the generated ORDERID sent to Worldline. Callbacks
    must resolve exactly one attempt once, making payment processing idempotent.
    """

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OBSOLETE = "obsolete"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (SUCCEEDED, "Succeeded"),
        (FAILED, "Failed"),
        (CANCELLED, "Cancelled"),
        (OBSOLETE, "Obsolete"),
    )

    registration = models.ForeignKey("evan.Registration", related_name="payment_attempts", on_delete=models.CASCADE)
    order_id = models.CharField(max_length=128, unique=True)
    expected_amount = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    payid = models.CharField(max_length=64, null=True, blank=True, unique=True)
    callback_data = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # noqa: D106
        db_table = "evan_log_registration_payment_attempt"
        indexes = [
            models.Index(fields=["registration", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.registration} - {self.order_id} - {self.status}"

    def mark_resolved(self, *, status: str, payid: str | None = None, callback_data: dict | None = None) -> None:
        """Transition the attempt to a terminal state.

        :param status: One of the terminal status constants.
        :param payid: Optional payid returned by Worldline.
        :param callback_data: Optional raw callback payload for audit/debugging.
        """
        self.status = status
        if payid:
            self.payid = payid
        if callback_data is not None:
            self.callback_data = callback_data
        self.resolved_at = timezone.now()


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, *args, **kwargs):
    if created and instance.status == Payment.SUCCEEDED:
        instance.registration.saldo = instance.registration.saldo + instance.amount
        instance.registration.save()

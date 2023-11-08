import uuid
from hashlib import sha256

from django.conf import settings
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import reverse

from .base import NonEditableMixin
from .rel.remarks import RemarksMixin
from .sessions import Session


def calculate_accompanying_fees(accompanying_data: dict) -> int:
    session_ids = accompanying_data.keys()
    fees = 0

    if session_ids:
        for session in Session.objects.filter(pk__in=session_ids):
            fees += session.extra_attendees_fee * len(accompanying_data[str(session.id)])

    return fees


class Registration(RemarksMixin, models.Model):
    """A registration for an event."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="registrations", on_delete=models.PROTECT)
    user = models.ForeignKey("evan.User", related_name="registrations", on_delete=models.PROTECT)
    sessions = models.ManyToManyField("evan.Session", related_name="registrations", blank=True)

    visa_requested = models.BooleanField(default=False)
    visa_sent = models.BooleanField(default=False)

    fee_type = models.CharField(max_length=16)
    base_fee = models.PositiveSmallIntegerField(default=0, editable=False)
    extra_fees = models.PositiveSmallIntegerField(default=0, editable=False)
    manual_extra_fees = models.PositiveSmallIntegerField(default=0)
    coupon = models.OneToOneField("evan.Coupon", null=True, blank=True, on_delete=models.PROTECT)
    invoice_requested = models.BooleanField(default=False)
    invoice_sent = models.BooleanField(default=False)
    paid = models.PositiveSmallIntegerField(default=0, editable=False)
    paid_via_invoice = models.PositiveSmallIntegerField(default=0)
    saldo = models.IntegerField(default=0, editable=False)

    is_accepted = models.BooleanField(default=True, null=True)
    extra_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        indexes = [
            models.Index(fields=["uuid"]),
        ]
        ordering = ["-id"]
        unique_together = ["event", "user"]

    def __str__(self) -> str:
        return f"{self.uuid} ({self.user})"

    def save(self, *args, **kwargs):
        """
        `base_fee` is only calculated when the registration is created.
        `extra_fees` are recalculated every time (accompanying persons, for example).
        """
        if not self.pk:
            self.is_accepted = True if self.event.accept_by_default else None

        is_early = self.is_early if self.pk else self.event.is_early
        key = (self.fee_type, is_early)
        self.base_fee = self.event.fees_dict.get(key, 0)

        try:
            self.extra_fees = calculate_accompanying_fees(self.extra_data["accompanying_persons"])
        except KeyError:
            pass

        self.saldo = -self.remaining_fee
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("registration:app", args=[self.uuid])

    def editable_by_user(self, user) -> bool:
        return self.user.id == user.id

    def viewable_by_user(self, user) -> bool:
        return self.user.id == user.id

    def get_certificate_url(self) -> str:
        return reverse("registration:certificate", args=[self.uuid])

    def get_payment_url(self) -> str:
        return reverse("registration:payment", args=[self.uuid])

    def get_payment_delegated_url(self) -> str:
        return reverse("registration:payment_delegated", args=[self.uuid, self.secret])

    def get_payment_result_url(self) -> str:
        return reverse("registration:payment_result", args=[self.uuid])

    def get_payment_delegated_result_url(self) -> str:
        return reverse("registration:payment_delegated_result", args=[self.uuid, self.secret])

    def get_receipt_url(self) -> str:
        return reverse("registration:receipt", args=[self.uuid])

    @property
    def is_early(self) -> bool:
        if not self.event.registration_early_deadline:
            return False
        return self.created_at <= self.event.registration_early_deadline

    @property
    def is_paid(self) -> bool:
        return self.saldo >= 0

    @property
    def is_paid_online(self) -> bool:
        return self.saldo >= 0 and self.paid > 0

    @property
    def remaining_fee(self) -> int:
        coupon_discount = self.coupon.value if self.coupon else 0
        return self.total_fee - self.paid - self.paid_via_invoice - coupon_discount

    @property
    def secret(self) -> str:
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()

    @property
    def total_fee(self) -> int:
        return self.base_fee + self.extra_fees + self.manual_extra_fees


@receiver(post_save, sender=Registration)
def registration_post_save(sender, instance, created, *args, **kwargs):
    pass
    # from evan.site.emails.registrations import RegistrationCreatedEmail

    if created:
        event = instance.event
        event.registrations_count = event.registrations.count()
        event.save()

        # RegistrationCreatedEmail(queryset=[instance]).send()


@receiver(m2m_changed, sender=Registration.sessions.through)
def registration_sessions_changed(sender, instance, **kwargs) -> None:
    if kwargs.get("action") == "post_add":
        logs = list(RegistrationLog.objects.filter(registration_id=instance.id).values_list("session_id", flat=True))
        new_logs = []

        for session in instance.sessions.exclude(id__in=logs).only("id"):
            new_logs.append(RegistrationLog(registration_id=instance.id, session_id=session.id))

        if new_logs:
            RegistrationLog.objects.bulk_create(new_logs)


class RegistrationLog(NonEditableMixin, models.Model):
    """
    In some occasions, it can be interesting to know when somebody first registered for an activity.
    If later an activity is unselected, this log shows when the initial registration was made.
    """

    registration = models.ForeignKey("evan.Registration", related_name="logs", on_delete=models.CASCADE)
    session = models.ForeignKey("evan.Session", related_name="logs", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # noqa: D106
        db_table = "evan_log_registration"
        unique_together = ["registration", "session"]

    def __str__(self) -> str:
        return f"{self.registration} - {self.session}"


class InvitationLetter(models.Model):
    """
    Information necessary to issue an invitation letter.
    """

    PAPER = "paper"
    POSTER = "poster"
    SUBMITTED_CHOICES = (
        (PAPER, "Paper"),
        (POSTER, "Poster"),
    )

    registration = models.OneToOneField(Registration, primary_key=True, related_name="letter", on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    passport_number = models.CharField(max_length=60)
    nationality = models.CharField(max_length=190)
    address = models.TextField()
    submitted = models.CharField(max_length=16, default="", blank=True, choices=SUBMITTED_CHOICES)
    submitted_title = models.TextField(default="", blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self) -> str:
        return f"{self.registration.uuid}"

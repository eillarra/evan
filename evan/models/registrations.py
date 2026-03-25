import uuid
from hashlib import sha256

from django.conf import settings
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import reverse

from .base import NonEditableMixin, TagsMixin
from .rel.remarks import RemarksMixin, append_remarks_tags


def calculate_accompanying_fees(registration: Registration) -> int:
    """
    Given a registration, calculate the fees for accompanying persons.
    Accompanying persons always pay the `session.extra_attendees_fee`.
    """
    extra_fees = 0
    social_events = registration.event.sessions.filter(is_social_event=True)

    for person in registration.extra_data.get("accompanying_persons", []):
        session_ids = person.get("selected_social_events", [])
        extra_fees += sum(session.extra_attendees_fee for session in social_events if session.id in session_ids)

    return extra_fees


def calculate_social_event_fees(registration: Registration) -> int:
    """
    Given a registration, check if selected fee includes social events.
    If not, sum the `session.extra_attendees_fee` for each selected social event.
    """
    extra_fees = 0
    included_social_events = registration.event.fees_dict[registration.fee_type].config.get(
        "included_social_events", []
    )

    try:
        social_events = registration.sessions.filter(is_social_event=True)

        for session in social_events:
            if session.id not in included_social_events:
                extra_fees += session.extra_attendees_fee
    except ValueError:
        pass

    return extra_fees


def calculate_registration_base_fee(registration: Registration) -> int:
    """
    Given a registration, calculate the base fee.
    The base fee is the sum of the early fee and the extra fees for accompanying persons.
    """
    fee = registration.event.fees_dict.get(registration.fee_type, None)

    if not fee:
        raise ValueError(f"Fee type {registration.fee_type} not found for event {registration.event}")

    is_early = registration.is_early if registration.pk else registration.event.is_early
    is_onsite = registration.is_onsite if registration.pk else registration.event.is_onsite

    if is_onsite:
        base_fee = fee.onsite_value if fee.onsite_value is not None else fee.value
    elif is_early:
        base_fee = fee.early_value if fee.early_value is not None else fee.value
    else:
        base_fee = fee.value

    base_fee += calculate_social_event_fees(registration)

    return base_fee


def get_registration_tags(obj: Registration, *, type: str = "all") -> list[str]:
    """For a registration, process the tags.

    :param obj: An instance of the Place class.
    :param type: The type of tags to process.
    :returns: A list of tags.
    """
    tags = obj.tags

    # remarks
    if type in {"all", "remarks"}:
        tags = append_remarks_tags(obj, tags=tags)

    return list(set(tags))


class Registration(RemarksMixin, TagsMixin, models.Model):
    """A registration for an event."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="registrations", on_delete=models.PROTECT)
    user = models.ForeignKey("evan.User", related_name="registrations", on_delete=models.PROTECT)
    sessions = models.ManyToManyField("evan.Session", related_name="registrations", blank=True)

    visa_requested = models.BooleanField(default=False)
    visa_sent = models.BooleanField(default=False)

    fee_type = models.CharField(max_length=64)
    base_fee = models.PositiveSmallIntegerField(default=0, editable=False)
    extra_fees = models.PositiveSmallIntegerField(default=0, editable=False)
    manual_extra_fees = models.PositiveSmallIntegerField(default=0)
    coupon = models.OneToOneField("evan.Coupon", null=True, blank=True, on_delete=models.PROTECT)
    invoice_requested = models.BooleanField(default=False)
    invoice_sent = models.BooleanField(default=False)
    paid = models.PositiveSmallIntegerField(default=0, editable=False)
    paid_via_invoice = models.PositiveSmallIntegerField(default=0)
    saldo = models.IntegerField(default=0, editable=False)
    no_show = models.BooleanField(default=False)

    is_accepted = models.BooleanField(default=True, null=True)
    extra_data = models.JSONField(default=dict)
    unique_hash = models.CharField(max_length=8, default="", blank=True)

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
            self.unique_hash = self.generate_unique_hash()

        self.base_fee = calculate_registration_base_fee(self)

        try:
            self.extra_fees = calculate_accompanying_fees(self)
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

    def get_certificate_url(self) -> str | None:
        if self.no_show:
            return None
        return reverse("registration:certificate", args=[self.uuid])

    def get_payment_url(self) -> str:
        return reverse("registration:payment", args=[self.uuid])

    def get_payment_delegated_url(self) -> str:
        return reverse("registration:payment_delegated", args=[self.uuid, self.secret])

    def get_payment_result_url(self) -> str:
        return reverse("registration:payment_result", args=[self.uuid])

    def get_payment_delegated_result_url(self) -> str:
        return reverse("registration:payment_delegated_result", args=[self.uuid, self.secret])

    def get_receipt_url(self) -> str | None:
        if not self.is_paid or self.paid <= 0:
            return None
        return reverse("registration:receipt", args=[self.uuid])

    def generate_unique_hash(self) -> str:
        """
        Generate a unique hash for the registration.
        This is used to later generate secret links for the registration.
        It can be regenerated if needed, for example to reset payment links.
        """
        return uuid.uuid4().hex[:8]

    @property
    def is_early(self) -> bool:
        if not self.event.registration_early_deadline:
            return False
        return self.created_at <= self.event.registration_early_deadline

    @property
    def is_onsite(self) -> bool:
        if not self.event.registration_onsite_deadline:
            return False
        return self.created_at > self.event.registration_deadline

    @property
    def is_paid(self) -> bool:
        return self.saldo >= 0

    @property
    def is_paid_online(self) -> bool:
        return self.saldo >= 0 and self.paid > 0

    @property
    def paid_via_coupon(self) -> int:
        if not self.coupon:
            return 0
        elif self.coupon.coverage == self.coupon.BASE_FEE:
            return min(self.coupon.value, self.base_fee)
        else:
            return min(self.coupon.value, self.total_fee)

    @property
    def remaining_fee(self) -> int:
        return self.total_fee - self.paid - self.paid_via_invoice - self.paid_via_coupon

    @property
    def secret(self) -> str:
        return sha256(f"{self.uuid}{settings.SECRET_KEY}".encode()).hexdigest()

    @property
    def total_fee(self) -> int:
        return self.base_fee + self.extra_fees + self.manual_extra_fees

    @property
    def url(self) -> str:
        return self.get_absolute_url()

    @classmethod
    def update_tags(cls, obj: Registration, *, type: str = "all") -> None:
        """Update tags for a student, without calling clean() on the model."""
        tags = get_registration_tags(obj, type=type)
        cls.objects.filter(pk=obj.pk).update(tags=tags)


@receiver(post_save, sender=Registration)
def registration_post_save(sender, instance, created, *args, **kwargs):
    if created:
        from evan.services.mailer.registrations import schedule_registration_email

        schedule_registration_email(instance, code="registration.created")

        event = instance.event
        event.registrations_count = event.registrations.count()
        event.save()


@receiver(m2m_changed, sender=Registration.sessions.through)
def registration_sessions_changed(sender, instance, **kwargs) -> None:
    if kwargs.get("action") == "post_add":
        logs = list(RegistrationLog.objects.filter(registration_id=instance.id).values_list("session_id", flat=True))
        new_logs = []

        for session in instance.sessions.exclude(id__in=logs).only("id"):
            new_logs.append(RegistrationLog(registration_id=instance.id, session_id=session.id))

        if new_logs:
            RegistrationLog.objects.bulk_create(new_logs)

    instance.base_fee = calculate_registration_base_fee(instance)
    instance.saldo = -instance.remaining_fee
    instance.save()


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

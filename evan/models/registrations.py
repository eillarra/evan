import uuid
from hashlib import sha256
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .base import NonEditableMixin, TagsMixin
from .rel.remarks import RemarksMixin, append_remarks_tags


if TYPE_CHECKING:
    from .events import Event


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


def enforce_session_capacity(session_ids: set[int], *, event: Event) -> None:
    """Raise ``ValueError`` if any of the given sessions is at capacity.

    Applies to any capped session (``Session.max_attendees``), not just social
    events - some events also have a detailed, non-social session selector.

    :param session_ids: The session IDs to check.
    :param event: The event the sessions belong to.
    :raises ValueError: If one of the sessions is already full.
    """
    if not session_ids:
        return

    for session in event.sessions.filter(id__in=session_ids, max_attendees__gt=0):
        if session.is_full:
            raise ValueError(f"Session '{session.title}' is full.")


def enforce_session_group_exclusivity(session_ids: set[int], *, registration: Registration) -> None:
    """Raise ``ValueError`` if a newly selected session's group conflicts with another selection.

    Sessions sharing the same ``extra_data.group`` value are mutually exclusive:
    a registrant may pick at most one session per group. This guard runs in the
    ``sessions`` M2M ``pre_add`` signal alongside ``enforce_session_capacity``.

    :param session_ids: The session IDs being added in this M2M operation.
    :param registration: The registration the sessions are being added to.
    :raises ValueError: If a newly added session shares a group with an already-selected session.
    """
    if not session_ids:
        return

    new_sessions = registration.event.sessions.filter(id__in=session_ids)
    existing_ids = set(registration.sessions.values_list("id", flat=True)) - session_ids
    existing_sessions = registration.event.sessions.filter(id__in=existing_ids)

    existing_groups = {
        session.extra_data.get("group") for session in existing_sessions if session.extra_data.get("group")
    }
    for session in new_sessions:
        group = session.extra_data.get("group")
        if group and group in existing_groups:
            raise ValueError(f"Session '{session.title}' conflicts with another selection in group '{group}'.")


def enforce_accompanying_person_session_capacity(
    registration: Registration, previous: Registration | None = None
) -> None:
    """Raise ``ValueError`` if an accompanying person is added to a full social event.

    Accompanying persons can only select social events. The main registrant's
    own session selections are enforced separately, via ``enforce_session_capacity``
    on the ``sessions`` M2M's ``pre_add`` signal, since they are saved after the
    registration row itself.

    :param registration: The registration being created or updated.
    :param previous: The previous state of the registration when updating, or None on create.
    :raises ValueError: If a newly selected social event is already full.
    """
    previous_person_session_ids: set[int] = set()
    if previous:
        for person in previous.extra_data.get("accompanying_persons", []):
            previous_person_session_ids.update(person.get("selected_social_events", []))

    new_person_session_ids: set[int] = set()
    for person in registration.extra_data.get("accompanying_persons", []):
        new_person_session_ids.update(person.get("selected_social_events", []))

    newly_added_ids = new_person_session_ids - previous_person_session_ids
    enforce_session_capacity(newly_added_ids, event=registration.event)


def enforce_fee_type_capacity(registration: Registration, previous: Registration | None = None) -> None:
    """Raise ``ValueError`` if the registration's fee type is already at capacity.

    A fee type is capped via ``Fee.config["max_registrations"]``. The count of
    non-rejected registrations for that fee type (excluding the current
    registration itself when updating) must stay below the configured cap.

    :param registration: The registration being created or updated.
    :param previous: The previous state of the registration when updating, or None on create.
    :raises ValueError: If the fee type is sold out (the cap is reached).
    """
    fee = registration.event.fees_dict.get(registration.fee_type, None)
    if not fee:
        return

    max_registrations = fee.config.get("max_registrations")
    if not max_registrations:
        return

    reserved_qs = registration.event.registrations.exclude(is_accepted=False).filter(fee_type=registration.fee_type)
    if previous and previous.pk:
        reserved_qs = reserved_qs.exclude(pk=previous.pk)

    if reserved_qs.count() >= max_registrations:
        raise ValueError(f"Fee type {registration.fee_type} is sold out.")


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
    invoice_address = models.TextField(blank=True, default="")
    paid = models.PositiveSmallIntegerField(default=0, editable=False)
    payid = models.CharField(max_length=64, blank=True, default="")
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
        previous = None
        if not self.pk:
            self.is_accepted = True if self.event.accept_by_default else None
            self.unique_hash = self.generate_unique_hash()
        else:
            previous = type(self).objects.get(pk=self.pk)

        enforce_fee_type_capacity(self, previous=previous)
        enforce_accompanying_person_session_capacity(self, previous=previous)
        self.base_fee = calculate_registration_base_fee(self)

        try:
            self.extra_fees = calculate_accompanying_fees(self)
        except KeyError:
            pass

        if previous and previous.remaining_fee != self.remaining_fee and previous.unique_hash == self.unique_hash:
            self.unique_hash = self.generate_unique_hash()

        self.saldo = -self.remaining_fee
        super().save(*args, **kwargs)

        if previous:
            previous_order_id = previous.get_current_payment_order_id()
            current_order_id = self.get_current_payment_order_id()
            if previous_order_id != current_order_id:
                self._obsolete_stale_payment_attempts(current_order_id=current_order_id)

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

    def get_payment_callback_url(self) -> str:
        return reverse("registration:payment_callback", args=[self.uuid])

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

    def get_current_payment_order_id(self) -> str | None:
        """Return the currently valid payment ORDERID for this registration.

        :returns: The active payment ORDERID or None when no payment is due.
        """
        if not self.pk or self.remaining_fee <= 0:
            return None

        from evan.services.payments.ugent_bridge import UGentBridge

        return UGentBridge.generate_order_id(self.pk, self.remaining_fee, self.unique_hash)

    def _obsolete_stale_payment_attempts(self, *, current_order_id: str | None) -> None:
        """Mark older pending payment attempts as obsolete.

        :param current_order_id: The only still-valid ORDERID, if any.
        """
        from .payments import RegistrationPaymentAttempt

        attempts = RegistrationPaymentAttempt.objects.filter(
            registration=self,
            status=RegistrationPaymentAttempt.PENDING,
        )
        if current_order_id is not None:
            attempts = attempts.exclude(order_id=current_order_id)

        attempts.update(
            status=RegistrationPaymentAttempt.OBSOLETE,
            resolved_at=timezone.now(),
        )

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
    action = kwargs.get("action")

    if action == "pre_add":
        pk_set = kwargs.get("pk_set") or set()
        newly_added_ids = pk_set - set(instance.sessions.values_list("id", flat=True))
        enforce_session_capacity(newly_added_ids, event=instance.event)
        enforce_session_group_exclusivity(newly_added_ids, registration=instance)
        return

    if action == "post_add":
        logs = list(RegistrationLog.objects.filter(registration_id=instance.id).values_list("session_id", flat=True))
        new_logs = []

        for session in instance.sessions.exclude(id__in=logs).only("id"):
            new_logs.append(RegistrationLog(registration_id=instance.id, session_id=session.id))

        if new_logs:
            RegistrationLog.objects.bulk_create(new_logs)

    if action in {"post_add", "post_remove", "post_clear"}:
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
        try:
            return f"{self.registration.uuid}"
        except type(self).registration.RelatedObjectDoesNotExist:
            # During admin inline deletion Django may stringify a detached instance.
            return f"Invitation letter ({self.registration_id or 'unlinked'})"

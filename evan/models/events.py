from datetime import UTC, datetime
from typing import TYPE_CHECKING

from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django_countries.fields import CountryField

from .documents.badges import get_validated_badges_configuration
from .documents.events import (
    get_validated_event_configuration,
    get_validated_event_extra_data,
    get_validated_event_registration_configuration,
)
from .emails import EmailTemplate
from .rel.files import File, FilesMixin
from .rel.links import LinksMixin
from .rel.permissions import Permission, PermissionsMixin
from .users import User


if TYPE_CHECKING:
    from evan.models.fees import Fee


def validate_event_dates(event):
    if event.end_date < event.start_date:
        raise ValidationError("End date cannot be earlier than start date.")
    if event.start_date <= event.registration_start_date:
        raise ValidationError("Registrations should open before the event starts.")
    if event.registration_deadline.date() < event.registration_start_date:
        raise ValidationError("Registrations cannot end before they start...")

    if event.registration_early_deadline:
        if event.registration_early_deadline.date() < event.registration_start_date:
            raise ValidationError("Early deadline cannot be earlier than registration start date.")
        if event.registration_early_deadline > event.registration_deadline:
            raise ValidationError("Early deadline cannot be later than registration deadline.")

    if event.registration_onsite_deadline and event.registration_onsite_deadline <= event.registration_deadline:
        raise ValidationError("On-site deadline must be later than the regular registration deadline.")


def validate_event_day(day):
    if day.date < day.event.start_date or day.date > day.event.end_date:
        raise ValidationError("Please check the date: it should be between the start and end dates of the event.")


def _guard_payments(event: Event) -> str | None:
    """Explain why the payments module cannot be disabled, or None when it can.

    :param event: The event whose payments data is checked.
    :returns: A human-readable explanation, or None when the module holds no data.
    """
    if event.fees.exists():
        return "the event has fees configured"
    if event.coupons.exists():
        return "the event has coupons configured"
    if event.registrations.filter(paid__gt=0).exists():
        return "the event has paid registrations"

    from evan.models.payments import RegistrationPaymentAttempt

    if RegistrationPaymentAttempt.objects.filter(registration__event=event).exists():
        return "the event has payment attempts"

    return None


def _guard_papers(event: Event) -> str | None:
    """Explain why the papers module cannot be disabled, or None when it can.

    :param event: The event whose papers data is checked.
    :returns: A human-readable explanation, or None when the module holds no data.
    """
    if event.papers.exists():
        return "the event has papers"
    if event.abstracts.exists():
        return "the event has abstracts"

    return None


def _guard_program(event: Event) -> str | None:
    """Explain why the program module cannot be disabled, or None when it can.

    :param event: The event whose program data is checked.
    :returns: A human-readable explanation, or None when the module holds no data.
    """
    if event.sessions.exists():
        return "the event has sessions"
    if event.tracks.exists() or event.topics.exists() or event.venues.exists():
        return "the event has tracks, topics or venues"

    return None


def _guard_content(event: Event) -> str | None:
    """Explain why the content module cannot be disabled, or None when it can.

    :param event: The event whose content data is checked.
    :returns: A human-readable explanation, or None when the module holds no data.
    """
    if event.contents.exists():
        return "the event has contents"
    if event.sponsors.exists():
        return "the event has sponsors"
    if event.albums.exists():
        return "the event has albums"
    if event.keynotes.exists():
        return "the event has keynotes"

    return None


def _guard_communications(event: Event) -> str | None:
    """Explain why the communications module cannot be disabled, or None when it can.

    :param event: The event whose communications data is checked.
    :returns: A human-readable explanation, or None when the module holds no data.
    """
    if event.email_plans.exists():
        return "the event has email plans"

    return None


MODULES: dict[str, object] = {
    "payments": _guard_payments,
    "content": _guard_content,
    "program": _guard_program,
    "papers": _guard_papers,
    "communications": _guard_communications,
}


class EventQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(end_date__gte=timezone.now().date()).order_by("end_date")

    def listed(self):
        return self.filter(listing_status=Event.ListingStatus.LISTED)


class EventManager(models.Manager.from_queryset(EventQuerySet)):
    """Manager for Event, combining upcoming() and listed() as chainable queryset methods."""


class RegistrationAudience(models.TextChoices):
    """Who may register for an event."""

    PUBLIC = "public", "Public"
    UGENT_ONLY = "ugent_only", "UGent only"


class ListingStatus(models.TextChoices):
    """Moderation state of an event's public listing."""

    PENDING_REVIEW = "pending_review", "Pending review"
    LISTED = "listed", "Listed"
    DECLINED = "declined", "Declined"


class Event(FilesMixin, LinksMixin, PermissionsMixin, models.Model):
    """An event."""

    RegistrationAudience = RegistrationAudience
    ListingStatus = ListingStatus

    is_virtual = models.BooleanField(default=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    full_name = models.CharField(max_length=200)
    city = models.CharField(max_length=160)
    country = CountryField()
    presentation = models.TextField(default="", blank=True)
    website = models.URLField(default="", blank=True)
    hashtag = models.CharField(max_length=32, default="", blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_early_deadline = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField()
    registration_onsite_deadline = models.DateTimeField(null=True, blank=True)

    social_event_bundle_fee = models.PositiveSmallIntegerField(default=0)
    signature = models.TextField(default="", blank=True)
    email = models.EmailField(default="", blank=True)

    registration_audience = models.CharField(
        max_length=32,
        choices=RegistrationAudience.choices,
        default=RegistrationAudience.PUBLIC,
    )
    listing_status = models.CharField(
        max_length=32,
        choices=ListingStatus.choices,
        default=ListingStatus.PENDING_REVIEW,
    )
    listing_decided_by = models.ForeignKey(
        "evan.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="listing_decisions"
    )
    listing_decided_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(default="", blank=True)

    config = models.JSONField(default=dict)
    registration_config = models.JSONField(default=dict)
    extra_data = models.JSONField(default=dict)
    custom_fields = models.JSONField(default=dict)  # TODO: remove this field

    registrations_count = models.PositiveIntegerField(default=0)
    accept_by_default = models.BooleanField(default=True)

    objects = EventManager()

    class Meta:  # noqa: D106
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["start_date", "end_date"]),
        ]
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        try:
            self.config = get_validated_event_configuration(self.config or {})
        except ValueError as exc:
            raise ValidationError({"config": [str(exc)]}) from exc

        try:
            self.registration_config = get_validated_event_registration_configuration(self.registration_config or {})
        except ValueError as exc:
            raise ValidationError({"config": [str(exc)]}) from exc

        try:
            self.extra_data = get_validated_event_extra_data(self.extra_data or {})
        except ValueError as exc:
            raise ValidationError({"extra_data": [str(exc)]}) from exc

        super().save(*args, **kwargs)

    def clean(self) -> None:
        validate_event_dates(self)

        if self.hashtag:
            self.hashtag = self.hashtag[1:] if self.hashtag.startswith("#") else self.hashtag

        self.clean_modules()

    def clean_modules(self) -> None:
        """Refuse disabling a module that already holds data.

        :raises ValidationError: When a module being switched off still has data.
        """
        if not self.pk:
            return

        previous_modules = type(self).objects.filter(pk=self.pk).values_list("config", flat=True).first() or {}
        previous = previous_modules.get("modules", {}) if isinstance(previous_modules, dict) else {}
        current = (self.configuration or {}).get("modules", {})

        for key, guard in MODULES.items():
            if previous.get(key, False) and not current.get(key, False):
                explanation = guard(self)
                if explanation:
                    raise ValidationError(
                        {
                            "config": [
                                f"The '{key}' module cannot be disabled because {explanation}. "
                                "The existing data is preserved; re-enable the module to use it again."
                            ]
                        }
                    )

    def module_enabled(self, key: str) -> bool:
        """Check whether an optional module is enabled for this event.

        :param key: The module key (one of the keys in the MODULES registry).
        :returns: True when the module is enabled, False otherwise.
        :raises KeyError: If the key is not a known module.
        """
        if key not in MODULES:
            raise KeyError(f"Unknown module: {key}")
        return bool((self.configuration or {}).get("modules", {}).get(key, False))

    def get_absolute_url(self) -> str:  # noqa: DJ012
        return reverse("event:app", args=[self.code])

    def get_manage_url(self) -> str:  # noqa: DJ012
        """Return the URL of the event's organizer console."""
        return reverse("event:manage", args=[self.code])

    def get_api_url(self) -> str:
        return reverse("v1:event-detail", args=[self.code])

    def get_registration_url(self) -> str:  # noqa: DJ012
        return reverse("registration:app", args=[self.code])

    def get_registration_preview_url(self) -> str:  # noqa: DJ012
        """Return the URL for the event manager's registration form preview."""
        return reverse("event:registration_preview", args=[self.code])

    def get_email_template(self, *, code: str) -> EmailTemplate | None:
        """Get an email template for an event.

        :param code: The code of the email template to get.
        :returns: The email template for the event and code or the default one, or None if not found.
        """
        try:
            return EmailTemplate.objects.get(code=code, event=self)
        except EmailTemplate.DoesNotExist:
            try:
                return EmailTemplate.objects.get(code=code, event=None)
            except EmailTemplate.DoesNotExist:
                return None

    @property
    def allows_invoices(self) -> bool:
        return self.ugent_bridge.get("allow_invoices", False)

    @property
    def allows_payments(self) -> bool:
        if "salt" not in self.ugent_bridge:
            return False
        if self.ugent_bridge.get("activation_date", None):
            activation_date = self.ugent_bridge.get("activation_date")
            if activation_date:
                activation_date = datetime.strptime(activation_date, "%Y-%m-%d").date()
            return activation_date is not None and activation_date <= timezone.now().date()
        return True

    @property
    def badges_configuration(self) -> dict:
        badges_data = self.extra_data.get("badges", {})
        valid_fee_types = list(self.fees.values_list("type", flat=True))
        return get_validated_badges_configuration(badges_data, valid_fee_types)

    @property
    def configuration(self) -> dict:
        return get_validated_event_configuration(self.config or {})

    def get_logo_file(self) -> File | None:
        """Return the event's logo file to print on badges.

        The logo is a public file tagged ``logo``. Only SVG logos are
        returned, since the badge PDF renders them as vectors.

        :returns: The logo File, or None when no SVG logo is attached.
        """
        for file in self.files.filter(type=File.PUBLIC).order_by("pk"):
            if "logo" in (file.tags or []) and file.file.name.lower().endswith(".svg"):
                return file
        return None

    @property
    def contact_email(self) -> str:
        return self.email or "evan@ugent.be"

    @property
    def ugent_bridge(self) -> dict:
        if self.configuration["payments"] and self.configuration["payments"]["type"] == "ugent":
            return self.configuration["payments"]
        return {}

    @property
    def registration_configuration(self) -> dict:
        return get_validated_event_registration_configuration(self.registration_config or {})

    @property
    def is_listed(self) -> bool:
        return self.listing_status == self.ListingStatus.LISTED

    @property
    def is_active(self) -> bool:
        return self.start_date <= timezone.now().date() <= self.end_date

    @property
    def is_closed(self) -> bool:
        return timezone.now().date() > self.end_date

    ### vvvvvvvv Below needs to be checked/refactored vvvvvvvv ###

    @property
    def dates_display(self) -> str:
        two_months = self.start_date.month != self.end_date.month
        if two_months:
            return f"{date_filter(self.start_date, 'F j')} - {date_filter(self.end_date, 'F j, Y')}"
        else:
            return f"{date_filter(self.start_date, 'F j')}-{date_filter(self.end_date, 'j, Y')}"

    def editable_by_user(self, user) -> bool:
        return self.can_be_managed_by(user)

    def can_be_managed_by(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

    def files_viewable_by_user(self, user) -> bool:
        """Check if the event files are viewable by a user (managers or accepted attendees)."""
        return self.editable_by_user(user) or self.registrations.filter(user_id=user.id, is_accepted=True).exists()

    def get_abstract_url(self) -> str:
        return "".join(["//", get_current_site(None).domain, reverse("abstract:redirect", args=[self.code])])

    @property
    def has_social_event_bundle(self) -> bool:
        return self.social_event_bundle_fee > 0

    @property
    def is_early(self) -> bool:
        if not self.registration_early_deadline:
            return False
        return timezone.now() <= self.registration_early_deadline

    @property
    def is_onsite(self) -> bool:
        if not self.registration_onsite_deadline:
            return False
        now = timezone.now()
        return now > self.registration_deadline and now <= self.registration_onsite_deadline

    @property
    def is_open_for_registration(self) -> bool:
        now = timezone.now()
        end = self.registration_onsite_deadline or self.registration_deadline
        return self.registration_start_date <= now.date() and now <= end

    @cached_property
    def abstracts_config(self) -> dict:
        """Return the ``abstracts`` section of ``custom_fields`` as a dict.

        :returns: The abstracts configuration dict, or an empty dict when absent.
        """
        config = self.custom_fields.get("abstracts", {})
        return config if isinstance(config, dict) else {}

    @property
    def is_open_for_abstract_submission(self) -> bool:
        try:
            config = self.abstracts_config
            now = timezone.now()
            start_date = datetime.strptime(config["submission_start_date"], "%Y-%m-%d")
            deadline = datetime.strptime(config["submission_deadline"], "%Y-%m-%dT%H:%M")
            return start_date.replace(tzinfo=UTC).date() <= now.date() and now <= deadline.replace(tzinfo=UTC)
        except KeyError, TypeError, ValueError:
            return False

    @cached_property
    def abstract_reviewers(self) -> QuerySet[User]:
        try:
            reviewer_ids = [r["id"] for r in self.abstracts_config["reviewers"]]
            return User.objects.filter(id__in=reviewer_ids)
        except KeyError, TypeError:
            return User.objects.none()

    @cached_property
    def fees_dict(self) -> dict[int, Fee]:
        if not hasattr(self, "_fees"):
            self._fees = {f.type: f for f in self.fees.all()}  # type: ignore
        return self._fees

    @classmethod
    def objects_for_user(cls, user):
        return cls.objects.filter(acl__user=user)


@receiver(post_save, sender=Event)
def event_post_save(sender, instance: Event, created: bool, **kwargs) -> None:
    """Notify the platform team when a new event is created and awaits review.

    :param instance: The event that was saved.
    :param created: True when the event was just created.
    """
    if created:
        from evan.services.listing import notify_team_of_pending_review

        notify_team_of_pending_review(instance)

from datetime import datetime

import pytz
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django_countries.fields import CountryField

from .permissions import Permission


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


def validate_event_day(day):
    if day.date < day.event.start_date or day.date > day.event.end_date:
        raise ValidationError("Please check the date: it should be between the start and end dates of the event.")


class EventManager(models.Manager):
    def upcoming(self):
        return self.filter(end_date__gte=timezone.now().date()).order_by("end_date")


class Event(models.Model):
    """
    An event.
    """

    SUPPORTED_CURRENCIES = (("EUR", "Euro"),)  # https://stripe.com/docs/currencies

    is_virtual = models.BooleanField(default=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    full_name = models.CharField(max_length=200)
    city = models.CharField(max_length=160)
    country = CountryField()
    presentation = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    hashtag = models.CharField(max_length=32, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_early_deadline = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField()

    wbs_element = models.CharField(max_length=32, null=True, blank=True)
    ingenico_salt = models.CharField(max_length=200, null=True, blank=True)
    allows_invoices = models.BooleanField(default=True)
    payments_activation = models.DateTimeField(null=True, blank=True)
    test_mode = models.BooleanField(default=True, editable=False)
    social_event_bundle_fee = models.PositiveSmallIntegerField(default=0)
    signature = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    acl = GenericRelation("evan.Permission")
    files = GenericRelation("evan.File")

    config = models.JSONField(default=dict)
    custom_data = models.JSONField(default=dict)
    custom_fields = models.JSONField(default=dict)

    registrations_count = models.PositiveIntegerField(default=0)
    accept_by_default = models.BooleanField(default=True)

    objects = EventManager()

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["start_date", "end_date"]),
        ]
        ordering = ("-start_date",)

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        validate_event_dates(self)
        if self.hashtag:
            self.hashtag = self.hashtag[1:] if self.hashtag.startswith("#") else self.hashtag

    @property
    def dates_display(self) -> str:
        two_months = self.start_date.month != self.end_date.month
        if two_months:
            return f'{date_filter(self.start_date, "F j")} - {date_filter(self.end_date, "F j, Y")}'
        else:
            return f'{date_filter(self.start_date, "F j")}-{date_filter(self.end_date, "j, Y")}'

    def editable_by_user(self, user) -> bool:
        return self.can_be_managed_by(user)

    def can_be_managed_by(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

    def files_viewable_by_user(self, user) -> bool:
        return self.editable_by_user(user) or self.registrations.filter(user_id=user.id).exists()

    def get_absolute_url(self) -> str:
        return reverse("event:app", args=[self.code])

    def get_abstract_url(self) -> str:
        return "".join(["//", get_current_site(None).domain, reverse("abstract:redirect", args=[self.code])])

    def get_registration_url(self) -> str:
        return "".join(["//", get_current_site(None).domain, reverse("registration:redirect", args=[self.code])])

    @property
    def allows_payments(self) -> bool:
        if self.ingenico_salt is None:
            return False
        if self.payments_activation:
            return self.payments_activation <= timezone.now()
        return True

    @property
    def has_social_event_bundle(self) -> bool:
        return self.social_event_bundle_fee > 0

    @property
    def is_active(self) -> bool:
        return self.start_date <= timezone.now().date() <= self.end_date

    @property
    def is_closed(self) -> bool:
        return timezone.now().date() > self.end_date

    @property
    def is_early(self) -> bool:
        if not self.registration_early_deadline:
            return False
        return timezone.now() <= self.registration_early_deadline

    @property
    def is_open_for_registration(self) -> bool:
        now = timezone.now()
        return self.registration_start_date <= now.date() and now <= self.registration_deadline

    @property
    def is_open_for_abstract_submission(self) -> bool:
        try:
            now = timezone.now()
            start_date = datetime.strptime(self.custom_data["abstracts"]["submission_start_date"], "%Y-%m-%d")
            deadline = datetime.strptime(self.custom_data["abstracts"]["submission_deadline"], "%Y-%m-%dT%H:%M")
            return start_date.replace(tzinfo=pytz.UTC).date() <= now.date() and now <= deadline.replace(tzinfo=pytz.UTC)
        except Exception:
            return False

    @cached_property
    def abstract_reviewers(self) -> QuerySet:
        try:
            reviewer_ids = [r["id"] for r in self.custom_data["abstracts"]["reviewers"]]
            return get_user_model().objects.filter(id__in=reviewer_ids)
        except Exception:
            return get_user_model().objects.none()

    @cached_property
    def fees_dict(self):
        if not hasattr(self, "_fees"):
            self._fees = {(f[0], f[1]): f[2] for f in self.fees.values_list("type", "is_early", "value")}
        return self._fees

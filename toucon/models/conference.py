import json

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.utils import timezone
from django_countries.fields import CountryField

from .permission import Permission


def validate_conference_dates(conference):
    if conference.end_date < conference.start_date:
        raise ValidationError('End date cannot be earlier than start date.')
    if conference.start_date <= conference.registration_start_date:
        raise ValidationError('Registrations should open before the conference starts.')
    if conference.registration_deadline.date() < conference.registration_start_date:
        raise ValidationError('Registrations cannot end before they start...')

    if conference.registration_early_deadline:
        if conference.registration_early_deadline.date() < conference.registration_start_date:
            raise ValidationError('Early deadline cannot be earlier than registration start date.')
        if conference.registration_early_deadline > conference.registration_deadline:
            raise ValidationError('Early deadline cannot be later than registration deadline.')


def validate_conference_day(day):
    if day.date < day.conference.start_date or day.date > day.conference.end_date:
        raise ValidationError('Please check the date: it should be between the start and end dates of the conference.')


class Conference(models.Model):
    """
    A conference.
    """
    SUPPORTED_CURRENCIES = (  # https://stripe.com/docs/currencies
        ('EUR', 'Euro'),
    )

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    full_name = models.CharField(max_length=160)
    city = models.CharField(max_length=160)
    country = CountryField()
    presentation = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    hashtag = models.CharField(max_length=16, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_early_deadline = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField()
    acl = GenericRelation('toucon.Permission')

    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default='EUR')
    badge = models.TextField(null=True, blank=True, default='{}')

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        validate_conference_dates(self)
        if self.hashtag:
            self.hashtag = self.hashtag[1:] if self.hashtag.startswith('#') else self.hashtag

    @property
    def date_range(self) -> str:
        return '{0} - {1}'.format(date_filter(self.start_date, 'j'), date_filter(self.end_date, 'j F Y'))

    def editable_by_user(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

    def get_absolute_url(self) -> str:
        return reverse('conference:app', args=[self.code])

    @property
    def is_active(self) -> bool:
        return self.start_date <= timezone.now().date() <= self.end_date

    @property
    def is_closed(self) -> bool:
        return timezone.now().date() > self.end_date

    @property
    def is_open_for_registration(self) -> bool:
        now = timezone.now()
        return self.registration_start_date <= now.date() and now <= self.registration_deadline

    @property
    def json_badge(self):
        return json.loads(self.badge)


class Day(models.Model):
    """
    Conference days: useful for registrations.
    """
    conference = models.ForeignKey(Conference, related_name='days', on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=190)

    class Meta:
        indexes = [
            models.Index(fields=['conference', 'date']),
        ]
        ordering = ('date',)

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.name, date_filter(self.date, 'D, N j'))

    def clean(self) -> None:
        validate_conference_day(self)

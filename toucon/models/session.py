from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from typing import List

from toucon.models import Permission


def validate_date(date, conference) -> None:
    if date < conference.start_date or date > conference.end_date:
        raise ValidationError('Date is not valid for this conference.')


class Session(models.Model):
    conference = models.ForeignKey('toucon.Conference', related_name='sessions', on_delete=models.CASCADE)
    organizers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='organized_sessions')
    date = models.DateField()
    track = models.ForeignKey('toucon.Track', related_name='sessions', null=True, on_delete=models.SET_NULL)
    room = models.ForeignKey('toucon.Room', related_name='sessions', null=True, blank=True, on_delete=models.SET_NULL)
    start_at = models.TimeField(null=True, blank=True)
    end_at = models.TimeField(null=True, blank=True)
    title = models.CharField(max_length=190)
    summary = models.TextField(null=True, blank=True)
    topics = models.ManyToManyField('toucon.Topic', blank=True, related_name='sessions')
    website = models.URLField(null=True, blank=True)
    image = models.FileField(upload_to='public/sympo/activity', null=True, blank=True)
    max_attendees = models.PositiveSmallIntegerField(default=0, help_text='Leave on `0` for non limiting.')
    extra_attendees_fee = models.PositiveSmallIntegerField(default=0)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acl = GenericRelation('toucon.Permission')

    class Meta:
        indexes = [
            models.Index(fields=['conference', 'date']),
            models.Index(fields=['conference', 'track']),
        ]
        ordering = ['date', 'start_at', 'end_at']

    def clean(self) -> None:
        validate_date(self.date, self.conference)

    def __str__(self) -> str:
        return self.title

    @staticmethod
    def autocomplete_search_fields() -> List[str]:
        return ['title__icontains']

    def editable_by_user(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

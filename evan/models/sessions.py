from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models

from evan.models import Permission


def validate_date(date, event) -> None:
    if date < event.start_date or date > event.end_date:
        raise ValidationError('Date is not valid for this event.')


class Session(models.Model):
    event = models.ForeignKey('evan.Event', related_name='sessions', on_delete=models.CASCADE)
    organizers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='organized_sessions')
    date = models.DateField()
    track = models.ForeignKey('evan.Track', related_name='sessions', null=True, on_delete=models.SET_NULL)
    room = models.ForeignKey('evan.Room', related_name='sessions', null=True, blank=True, on_delete=models.SET_NULL)
    start_at = models.TimeField(null=True, blank=True)
    end_at = models.TimeField(null=True, blank=True)
    title = models.CharField(max_length=190)
    summary = models.TextField(null=True, blank=True)
    topics = models.ManyToManyField('evan.Topic', blank=True, related_name='sessions')
    website = models.URLField(null=True, blank=True)
    image = models.FileField(upload_to='public/sympo/activity', null=True, blank=True)
    max_attendees = models.PositiveSmallIntegerField(default=0, help_text='Leave on `0` for non limiting.')
    extra_attendees_fee = models.PositiveSmallIntegerField(default=0)
    is_private = models.BooleanField(default=False)
    is_social_event = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acl = GenericRelation('evan.Permission')

    class Meta:
        indexes = [
            models.Index(fields=['event', 'date']),
            models.Index(fields=['event', 'track']),
        ]
        ordering = ('date', 'start_at', 'end_at')

    def clean(self) -> None:
        validate_date(self.date, self.event)

    def __str__(self) -> str:
        return self.title

    def editable_by_user(self, user) -> bool:
        return user.is_staff or self.acl.filter(user_id=user.id, level__gte=Permission.ADMIN).exists()

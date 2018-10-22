import decimal
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.template.defaultfilters import date as date_filter
from django.template.loader import get_template
from django.utils.timezone import localtime
from django.urls import reverse


class Coupon(models.Model):
    """
    Coupons are used to pay or reduce registration fees.
    """
    code = models.UUIDField(default=uuid.uuid4, editable=False)
    conference = models.ForeignKey('toucon.Conference', related_name='coupons', on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=190, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
        ]
        ordering = ['conference', 'id']

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.code, self.value)


class RegistrationManager(models.Manager):
    def with_profiles(self):
        return super().get_queryset().select_related('user__profile').order_by('user__first_name', 'user__last_name')


class Registration(models.Model):
    """
    A conference registration for a User.
    TODO: Fee calculation needs custom adaptations: see `sympo.helpers` and `sympo.forms.registration`.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    conference = models.ForeignKey('toucon.Conference', related_name='registrations', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='registrations', on_delete=models.CASCADE)
    # fee_profile = models.CharField(max_length=32, choices=FEE_PROFILES)
    days = models.ManyToManyField('toucon.Day', related_name='registrations')
    fee = models.PositiveIntegerField(default=0)
    saldo = models.IntegerField(default=0)
    coupon = models.OneToOneField(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    sessions = models.ManyToManyField('toucon.Session', related_name='registrations')
    visa_requested = models.BooleanField()
    visa_sent = models.BooleanField(default=False)
    invoice_requested = models.BooleanField(default=False)
    invoice_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RegistrationManager()

    class Meta:
        indexes = [
            models.Index(fields=['uuid']),
        ]
        ordering = ('-created_at',)
        unique_together = ('conference', 'user')

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.uuid, self.user)

    def editable_by_user(self, user) -> bool:
        return self.user_id == user.id

    def get_absolute_url(self) -> str:
        return reverse('registration:app', args=[self.uuid])

    @property
    def is_paid(self) -> bool:
        return self.saldo >= 0

    @property
    def pending_amount(self) -> str:
        symbols = {
            'EUR': '€',
            'USD': '$',
        }
        saldo = ("%.2f" % (-self.saldo / 100.00)) if self.conference.currency in ['EUR', 'USD'] else self.saldo
        return '{0}{1}'.format(symbols[self.conference.currency], saldo)


@receiver(post_save, sender=Registration)
def registration_post_save(sender, instance, created, *args, **kwargs):
    if created:
        msg = EmailMessage(
            '[{0}] Your registration for {1}'.format(instance.conference.hashtag.upper(), instance.conference),
            get_template('sympo/emails/registration.txt').render({
                'registration': instance
            }),
            to=[instance.user.profile.to_email],
            from_email='{0} <{1}>'.format(instance.conference.hashtag.upper(), settings.SYMPO_REGISTRATIONS_EMAIL)
        )
        msg.send()

        # if instance.visa_requested:
        #    visa_reminder_email(Registration.objects.filter(pk=instance.id))


@receiver(m2m_changed, sender=Registration.sessions.through)
def registration_sessions_changed(sender, instance, **kwargs) -> None:
    if kwargs.get('action') == 'post_add':
        logs = list(RegistrationLog.objects.filter(registration_id=instance.id).values_list('session_id', flat=True))
        new_logs = []

        for session in instance.sessions.exclude(id__in=logs).only('id'):
            new_logs.append(RegistrationLog(registration_id=instance.id, session_id=session.id))

        if new_logs:
            RegistrationLog.objects.bulk_create(new_logs)


class RegistrationLog(models.Model):
    """
    In some occasions, it can be interesting to know when somebody first registered for an activity.
    If later an activity is unselected, this log shows when the initial registration was made.
    """
    registration = models.ForeignKey(Registration, related_name='logs', on_delete=models.CASCADE)
    session = models.ForeignKey('toucon.Session', related_name='logs', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registration', 'session')

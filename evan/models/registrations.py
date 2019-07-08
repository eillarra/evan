import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.urls import reverse

from evan.functions import send_task
from .fees import Fee
from .metadata import Metadata


class RegistrationManager(models.Manager):

    def with_profiles(self):
        return super().get_queryset().select_related('user__profile').order_by('user__first_name', 'user__last_name')


class Registration(models.Model):
    """
    A event registration for a User.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey('evan.Event', related_name='registrations', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='registrations', on_delete=models.CASCADE)
    days = models.ManyToManyField('evan.Day', related_name='registrations')
    sessions = models.ManyToManyField('evan.Session', related_name='registrations')

    visa_requested = models.BooleanField(default=False)
    visa_sent = models.BooleanField(default=False)

    fee_type = models.CharField(max_length=8, default=Fee.REGULAR, choices=Fee.TYPE_CHOICES)
    base_fee = models.PositiveSmallIntegerField(default=0, editable=False)
    extra_fees = models.PositiveSmallIntegerField(default=0, editable=False)
    manual_extra_fees = models.PositiveSmallIntegerField(default=0)
    coupon = models.OneToOneField('evan.Coupon', null=True, blank=True, on_delete=models.SET_NULL)
    invoice_requested = models.BooleanField(default=False)
    invoice_sent = models.BooleanField(default=False)
    paid = models.PositiveSmallIntegerField(default=0, editable=False)
    paid_via_invoice = models.PositiveSmallIntegerField(default=0)
    saldo = models.IntegerField(default=0, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RegistrationManager()

    class Meta:
        indexes = [
            models.Index(fields=['uuid']),
        ]
        ordering = ('-created_at',)
        unique_together = ('event', 'user')

    def save(self, *args, **kwargs):
        """
        `base_fee` is only calculated when the registration is created.
        `extra_fees` are recalculated every time (accompanying persons, for example).
        """
        is_early = self.is_early if self.pk else self.event.is_early
        key = (self.fee_type, is_early) if self.fee_type != Fee.ONE_DAY else (self.fee_type, False)
        self.base_fee = self.event.fees_dict[key] if key in self.event.fees_dict else 0
        self.extra_fees = self.event.social_event_bundle_fee * self.accompanying_persons.count()
        self.saldo = -self.remaining_fee
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.uuid} ({self.user})'

    def editable_by_user(self, user) -> bool:
        return self.user_id == user.id and not self.event.is_closed

    def viewable_by_user(self, user) -> bool:
        return self.user_id == user.id

    def get_absolute_url(self) -> str:
        return reverse('registration:app', args=[self.uuid])

    def get_certificate_url(self) -> str:
        return reverse('registration:certificate', args=[self.uuid])

    def get_payment_url(self) -> str:
        return reverse('registration:payment', args=[self.uuid])

    def get_payment_result_url(self) -> str:
        return reverse('registration:payment_result', args=[self.uuid])

    def get_receipt_url(self) -> str:
        return reverse('registration:receipt', args=[self.uuid])

    @property
    def is_early(self) -> bool:
        if not self.event.registration_early_deadline:
            return False
        return self.created_at <= self.event.registration_early_deadline

    @property
    def is_paid(self) -> bool:
        return self.saldo >= 0

    @property
    def remaining_fee(self):
        coupon_discount = self.coupon.value if self.coupon else 0
        return self.total_fee - self.paid - self.paid_via_invoice - coupon_discount

    @property
    def total_fee(self):
        return self.base_fee + self.extra_fees + self.manual_extra_fees


@receiver(post_save, sender=Registration)
def registration_post_save(sender, instance, created, *args, **kwargs):
    if created:
        event = instance.event
        event.registrations_count = event.registrations.count()
        event.save()

        email = (
            '_emails/registrations_created.md.html',
            f'[{instance.event.hashtag}] Your registration / {instance.uuid}',
            'Ghent University <evan@ugent.be>',
            [instance.user.email],
            {
                'registration_uuid': str(instance.uuid),
                'registration_url': instance.get_absolute_url(),
                'visa_requested': instance.visa_requested,
                'event_city': instance.event.city,
                'event_name': instance.event.name,
            }
        )
        send_task('evan.tasks.emails.send_template_email', email)


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
    session = models.ForeignKey('evan.Session', related_name='logs', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registration', 'session')


class Person(models.Model):
    """
    Accompanying person.
    """
    registration = models.ForeignKey(Registration, related_name='accompanying_persons', on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    dietary = models.ForeignKey(Metadata, null=True, blank=True, on_delete=models.SET_NULL,
                                limit_choices_to={'type': Metadata.MEAL_PREFERENCE},
                                related_name='person_' + Metadata.MEAL_PREFERENCE)


@receiver(post_save, sender=Person)
@receiver(post_delete, sender=Person)
def person_post_update(sender, instance, *args, **kwargs):
    instance.registration.save()


class InvitationLetter(models.Model):
    """
    Information necessary to issue an invitation letter.
    """
    PAPER = 'paper'
    POSTER = 'poster'
    SUBMITTED_CHOICES = (
        (PAPER, 'Paper'),
        (POSTER, 'Poster'),
    )

    registration = models.OneToOneField(Registration, primary_key=True, related_name='letter', on_delete=models.CASCADE)
    name = models.CharField(max_length=190)
    passport_number = models.CharField(max_length=60)
    nationality = models.CharField(max_length=190)
    address = models.TextField()
    submitted = models.CharField(max_length=16, null=True, blank=True, default=None, choices=SUBMITTED_CHOICES)
    submitted_title = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.registration.uuid)

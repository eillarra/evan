from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Payment(models.Model):
    """
    A payment for the event. Payments are linked to registrations.
    """
    STRIPE_CHARGE = 'stripe_charge'
    STRIPE_REFUND = 'stripe_refund'
    TYPE_CHOICES = (
        (STRIPE_CHARGE, 'Stripe charge'),
        (STRIPE_REFUND, 'Stripe refund'),
    )

    SUCCEEDED = 'succeeded'
    PENDING = 'pending'
    FAILED = 'failed'
    STATUS_CHOICES = (  # https://stripe.com/docs/api#charge_object-status
        (SUCCEEDED, 'Succeeded'),
        (PENDING, 'Pending'),
        (FAILED, 'Failed'),
    )

    registration = models.ForeignKey('evan.Registration', related_name='payments', on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, default='EUR')
    amount = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=STRIPE_CHARGE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=FAILED)
    outcome = models.TextField(null=True, blank=True)
    stripe_id = models.CharField(max_length=64, null=True, blank=True)
    stripe_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, *args, **kwargs):
    if created and instance.status == Payment.SUCCEEDED:
        instance.registration.saldo = instance.registration.saldo + instance.amount
        instance.registration.save()

import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Coupon(models.Model):
    """
    Coupons are used to pay or reduce registration fees.
    """
    code = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey('evan.Event', related_name='coupons', on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=190, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
        ]
        ordering = ('event', 'id')

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.code, self.value)


class Fee(models.Model):
    """
    Coupons are used to pay or reduce registration fees.
    """
    REGULAR = 'regular'
    STUDENT = 'student'
    ONE_DAY = 'one_day'
    TYPE_CHOICES = (
        (REGULAR, 'Regular'),
        (STUDENT, 'Student'),
        (ONE_DAY, 'One day'),
    )

    event = models.ForeignKey('evan.Event', on_delete=models.CASCADE, related_name='fees')
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    value = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=190, null=True, blank=True)
    is_early = models.BooleanField(default=False)
    social_events_included = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['type', 'is_early']),
        ]

    def __str__(self) -> str:
        return f'{self.type} ({self.value})'

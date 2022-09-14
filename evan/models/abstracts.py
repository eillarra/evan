import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from typing import Optional


class Abstract(models.Model):
    """
    Paper abstract.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    event = models.ForeignKey("evan.Event", related_name="abstracts", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name="abstracts", on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)

    title = models.CharField(max_length=512)
    authors = models.CharField(max_length=512)
    abstract = models.TextField()
    files = GenericRelation("evan.File")

    custom_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"{self.uuid} ({self.user})"

    def editable_by_user(self, user) -> bool:
        return self.user_id == user.id

    def reviewer(self, user) -> bool:
        return self.editable_by_user(user) or self.event.editable_by_user(user)

    def viewable_by_user(self, user) -> bool:
        return (
            self.editable_by_user(user)
            or self.event.editable_by_user(user)
            or self.reviews.filter(user_id=user.id).exists()
        )

    def files_viewable_by_user(self, user) -> bool:
        return self.viewable_by_user(user) or (
            self.is_accepted and self.event.registrations.filter(user_id=user.id).exists()
        )

    def get_absolute_url(self) -> str:
        return reverse("abstract:app", args=[self.uuid])

    @property
    def file(self) -> Optional["evan.File"]:
        return self.files.first()


@receiver(post_save, sender=Abstract)
def registration_post_save(sender, instance, created, *args, **kwargs):
    from evan.site.emails.abstracts import AbstractCreatedEmail

    if created:
        AbstractCreatedEmail(queryset=[instance]).send()


class AbstractReview(models.Model):
    """
    Abstract review.
    """

    ASSIGNED = "assigned"
    REVIEWED = "reviewed"
    FINALIZED = "finalized"
    STATUS_CHOICES = (
        (ASSIGNED, "Assigned"),
        (REVIEWED, "Reviewed"),
        (FINALIZED, "Finalized"),
    )

    abstract = models.ForeignKey(Abstract, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name="abstract_reviews", on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=ASSIGNED)
    evaluation = models.TextField(null=True)
    comments = models.TextField(null=True, help_text="These can be shared with the applicant.")

    custom_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evan_abstract_review"
        unique_together = ("abstract", "user")

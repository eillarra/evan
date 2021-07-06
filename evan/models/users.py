from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_countries.fields import CountryField

from evan.functions import send_task


class ProfileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user")


class Profile(models.Model):
    """
    A user profile complements the base User model with extra information.
    """

    user = models.OneToOneField(get_user_model(), primary_key=True, related_name="profile", on_delete=models.CASCADE)
    position = models.CharField(max_length=190, null=True, blank=True)
    affiliation = models.CharField(max_length=190, null=True, blank=True)
    country = CountryField()
    updated_at = models.DateTimeField(auto_now=True)

    custom_data = models.JSONField(default=dict)

    objects = ProfileManager()

    def __str__(self) -> str:
        return f"{self.name}, {self.affiliation if self.affiliation else '-'}"

    def can_be_contacted(self) -> bool:
        return self.custom_data["connect"]

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def name(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def to_email(self) -> str:
        return f"{self.name} <{self.email}>"


@receiver(post_save, sender=get_user_model())
def post_save_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance, custom_data={"connect": True, "dietary": None, "gender": None, "special_needs": None}
        )
        send_task("evan.tasks.users.update_affiliation", (instance.id,))
    else:
        instance.profile.updated_at = timezone.now()
        instance.profile.save()

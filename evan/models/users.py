from typing import TYPE_CHECKING

from allauth.account.models import EmailAddress
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from tld import get_tld


if TYPE_CHECKING:
    from evan.models.events import Event


class AffiliationDomain(models.Model):
    """Reference model that links email domains to affiliations."""

    fld = models.CharField(max_length=190, unique=True)
    affiliation = models.CharField(max_length=190)
    country = CountryField()

    class Meta:  # noqa: D106
        db_table = "evan_log_fld"

    def __str__(self) -> str:
        return self.fld


class User(AbstractUser):
    """Custom user model."""

    affiliation = models.CharField(max_length=190, default="", blank=True)
    country = CountryField()
    extra_data = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}, {self.affiliation if self.affiliation else '-'}"

    def can_be_contacted(self) -> bool:
        return self.extra_data["connect"]

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def to_email(self) -> str:
        return f"{self.name} <{self.email}>"

    def events(self) -> models.QuerySet["Event"]:
        from evan.models.events import Event

        return Event.objects.filter(acl__user=self)


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if instance.email and not instance.affiliation:
        domain = get_tld(instance.email.split("@")[-1], as_object=True, fix_protocol=True)

        try:
            domain = AffiliationDomain.objects.get(fld=domain)
            instance.affiliation = instance.affiliation if instance.affiliation else domain.affiliation
            instance.country = instance.country if instance.country else domain.country
        except AffiliationDomain.DoesNotExist:
            pass


def find_user_by_email(email: str, verified: bool = True) -> User | None:
    try:
        return EmailAddress.objects.get(email__iexact=email, verified=verified).user
    except EmailAddress.DoesNotExist:
        return None


@receiver(pre_social_login)
def link_to_existing_user(sender, request, sociallogin, **kwargs):
    if sociallogin.is_existing:
        return

    # for "ugent" social accounts, we can use the email address to find the user
    if sociallogin.account.provider == "ugent":
        try:
            email = sociallogin.account.extra_data["mail"]
            user = find_user_by_email(email)
            if user:
                sociallogin.connect(request, user)
        except KeyError:
            return

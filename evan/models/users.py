from typing import TYPE_CHECKING

from allauth.account.models import EmailAddress
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from tld import Result, get_tld

from .documents.users import get_validated_extra_data


if TYPE_CHECKING:
    from evan.models.events import Event


USERNAME_COLLISION_MAX_RETRIES = 10
USERNAME_MAX_LENGTH = 150


def _username_with_suffix(base: str, suffix: int) -> str:
    """Append a numeric suffix to ``base``, truncating if needed to fit max length.

    :param base: The original username to extend.
    :param suffix: The positive integer to append.
    :returns: ``base + str(suffix)`` truncated to ``USERNAME_MAX_LENGTH``.
    """
    candidate = f"{base}{suffix}"
    if len(candidate) <= USERNAME_MAX_LENGTH:
        return candidate
    overflow = len(candidate) - USERNAME_MAX_LENGTH
    return f"{base[: len(base) - overflow]}{suffix}"


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

    def save(self, *args, **kwargs) -> None:
        try:
            self.extra_data = get_validated_extra_data(self.extra_data or {})
        except ValueError as exc:
            raise ValidationError({"extra_data": [str(exc)]}) from exc

        # CountryField is stored as a non-null database column.
        # Normalize explicit null values to empty string to avoid DB-level 500s.
        if self.country is None:
            self.country = ""

        # allauth validates username uniqueness in the signup form, but a
        # concurrent signup can insert the same username between validation
        # and save (TOCTOU race). Retry with a numeric suffix so the user gets
        # a close-but-unique username instead of a 500.
        original_username = self.username
        for attempt in range(USERNAME_COLLISION_MAX_RETRIES):
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return
            except IntegrityError:
                # Only retry on insert (new user) with a username. On update,
                # or for non-username IntegrityErrors, re-raise immediately.
                if not self._state.adding or not self.username:
                    self.username = original_username
                    raise
                self.username = _username_with_suffix(original_username, attempt + 1)
        self.username = original_username
        raise IntegrityError("Unable to generate a unique username")

    def __str__(self) -> str:
        return f"{self.name}, {self.affiliation if self.affiliation else '-'}"

    def can_be_contacted(self) -> bool:
        return self.extra_data.get("connect", True)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def to_email(self) -> str:
        return f"{self.name} <{self.email}>"

    def events(self) -> models.QuerySet[Event]:
        from evan.models.events import Event

        return Event.objects.filter(acl__user=self)


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if instance.email:
        res = get_tld(instance.email.split("@")[-1], as_object=True, fix_protocol=True)

        if isinstance(res, Result):
            try:
                domain = AffiliationDomain.objects.get(fld=res.fld)
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

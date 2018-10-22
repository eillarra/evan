from django.conf import settings
from django.db import models
from django_countries.fields import CountryField


class ProfileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('user')


class Profile(models.Model):
    """
    A user profile complements the base User model with extra information.
    """
    FEMALE = 'F'
    MALE = 'M'
    GENDER_CHOICES = (
        (FEMALE, 'Female'),
        (MALE, 'Male'),
    )

    NONE = 'none'
    VEGETARIAN = 'vegetarian'
    VEGAN = 'vegan'
    KOSHER = 'kosher'
    MUSLIM = 'muslim'
    INTOLERANT_GLUTEN = 'int_gluten'
    INTOLERANT_LACTOSE = 'int_lactose'
    ALLERGIC_CRUSTACEANS = 'al_crustaceans'
    ALLERGIC_CRUSTACEANS = 'al_peanuts'
    DIETARY_CHOICES = (
        (NONE, 'No special requirements'),
        (VEGETARIAN, 'Vegetarian'),
        (VEGAN, 'Vegan'),
        (KOSHER, 'Kosher'),
        (MUSLIM, 'Muslim'),
        (INTOLERANT_GLUTEN, 'Gluten intolerant'),
        (INTOLERANT_LACTOSE, 'Lactose intolerant'),
        (ALLERGIC_CRUSTACEANS, 'Allergic to crustaceans'),
        (ALLERGIC_CRUSTACEANS, 'Allergic to peanuts'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    gender = models.CharField(max_length=1, db_index=True, null=True, blank=True, choices=GENDER_CHOICES)
    dietary = models.CharField(max_length=16, db_index=True, null=True, blank=True, choices=DIETARY_CHOICES)
    affiliation = models.CharField(max_length=190)
    country = CountryField()

    objects = ProfileManager()

    def __str__(self) -> str:
        return '{0}, {1}'.format(self.name, self.affiliation)

    @property
    def name(self) -> str:
        return '{0} {1}'.format(self.user.first_name, self.user.last_name)

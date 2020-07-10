from django.core.cache import cache
from django.db import models
from django.db.utils import ProgrammingError
from typing import Dict, List


class Metadata(models.Model):
    """
    Metadata used by other models.
    """

    GENDER = "gender"
    MEAL_PREFERENCE = "meal_preference"
    TYPE_CHOICES = (
        (GENDER, "Gender"),
        (MEAL_PREFERENCE, "Meal preference"),
    )

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    value = models.CharField(max_length=64)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["type"])]
        ordering = ("type", "value")

    def __str__(self) -> str:
        return self.value


def get_cached_metadata_queryset() -> List[Metadata]:
    try:
        queryset = cache.get("cached_metadata_queryset")
        if not queryset:
            queryset = Metadata.objects.all()
            cache.set("cached_metadata_queryset", queryset, 30)
        return queryset
    except ProgrammingError:
        return []


def get_cached_metadata() -> Dict[int, Metadata]:
    try:
        objects = cache.get("cached_metadata_objects")
        if not objects:
            objects = {m.id: m for m in get_cached_metadata_queryset()}
            cache.set("cached_metadata_objects", objects, 30)
        return objects
    except ProgrammingError:
        return {}

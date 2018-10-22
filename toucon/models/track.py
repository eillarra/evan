from django.db import models
from django.utils.text import slugify
from typing import List


class Track(models.Model):
    conference = models.ForeignKey('toucon.Conference', related_name='tracks', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def autocomplete_search_fields() -> List[str]:
        return ['name__icontains']

    @property
    def slug(self) -> str:
        return slugify(self.name)

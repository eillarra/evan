from django.db import models
from django.utils.text import slugify


class Track(models.Model):
    event = models.ForeignKey('evan.Event', related_name='tracks', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('position', 'name')

    def __str__(self) -> str:
        return self.name

    @property
    def slug(self) -> str:
        return slugify(self.name)

from django.db import models

from .validators import validate_list_of_strings


class TagsMixin(models.Model):
    """A mixin to add tags to a model."""

    tags = models.JSONField(default=list, validators=[validate_list_of_strings])

    class Meta:  # noqa: D106
        abstract = True

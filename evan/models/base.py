from django.db import models

from .validators import validate_list_of_strings


class NonEditableMixin(models.Model):
    """Models with this mixin can only be created, never edited."""

    class Meta:  # noqa: D106
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            raise ValueError("This model is not editable.")
        super().save(*args, **kwargs)


class TagsMixin(models.Model):
    """A mixin to add tags to a model."""

    tags = models.JSONField(default=list, validators=[validate_list_of_strings])

    class Meta:  # noqa: D106
        abstract = True

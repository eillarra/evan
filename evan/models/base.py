from django.db import models


class NonEditableMixin(models.Model):
    """Models with this mixin can only be created, never edited."""

    class Meta:  # noqa: D106
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            raise ValueError("This model is not editable.")
        super().save(*args, **kwargs)

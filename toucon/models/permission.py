from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Permission(models.Model):
    """
    Conference auth model.
    Higher permission levels inherit lower permissions, simplifying queries.
    """
    OWNER = 9
    ADMIN = 5
    GUEST = 1
    LEVEL_CHOICES = (
        (OWNER, 'Owner'),
        (ADMIN, 'Administrator'),
        (GUEST, 'Guest'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name='perms', on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(db_index=True, choices=LEVEL_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='perms')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

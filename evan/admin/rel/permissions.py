from django.contrib.contenttypes.admin import GenericTabularInline

from evan.models.rel.permissions import Permission


class PermissionsInline(GenericTabularInline):
    model = Permission
    classes = ("collapse",)
    extra = 0
    # form
    raw_id_fields = ("user",)

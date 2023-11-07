from django.contrib.contenttypes.admin import GenericTabularInline

from evan.models import File


class FilesInline(GenericTabularInline):
    model = File
    classes = ("collapse",)
    extra = 0
    readonly_fields = ("tags",)

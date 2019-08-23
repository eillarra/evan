from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from evan.models import Image, Content


class ImagesInline(GenericTabularInline):
    model = Image
    classes = ('collapse',)
    extra = 0


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'key')
    list_filter = ('event',)

    inlines = (ImagesInline,)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('key', 'notes')
        return ()

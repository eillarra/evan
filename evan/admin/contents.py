from django.contrib import admin

from evan.models import Content

from .rel.files import FilesInline


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "key")
    list_filter = (("event", admin.RelatedOnlyFieldListFilter),)
    # form
    inlines = [FilesInline]

    def get_readonly_fields(self, request, obj=None):
        # Use getattr for safe access, defaulting to False if is_superuser doesn't exist
        if not getattr(request.user, "is_superuser", False):
            return ("event", "key", "config")
        return ()

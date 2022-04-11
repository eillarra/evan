from django.contrib import admin

from evan.models import Abstract
from .files import FilesInline


@admin.register(Abstract)
class AbstractAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user")
    list_filter = (("event", admin.RelatedOnlyFieldListFilter),)
    # form
    raw_id_fields = ("event", "user")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("is_accepted", "event", "user", "created_at", "updated_at"),
            },
        ),
        (
            "Abstract",
            {
                "fields": (
                    "title",
                    "authors",
                    "abstract",
                    "custom_data",
                ),
            },
        ),
    )
    inlines = (FilesInline,)

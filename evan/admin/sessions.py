from django.contrib import admin

from evan.models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    date_hierarchy = "start_at"
    list_display = (
        "id",
        "event",
        "title",
    )
    list_filter = (("event", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("title",)

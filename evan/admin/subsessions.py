from django.contrib import admin

from evan.models import Subsession


@admin.register(Subsession)
class SubsessionAdmin(admin.ModelAdmin):
    date_hierarchy = "start_at"
    list_display = (
        "id",
        "session",
        "title",
        "order",
        "start_at",
        "end_at",
    )
    list_filter = (("session__event", admin.RelatedOnlyFieldListFilter), "session")
    search_fields = ("title", "session__title")
    ordering = ("session", "order", "start_at")

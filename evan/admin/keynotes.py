from django.contrib import admin

from ..models import Keynote


@admin.register(Keynote)
class KeynoteAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "speaker", "event", "session", "subsession"]
    list_filter = ["event", "session", "topics"]
    search_fields = ["code", "title", "speaker", "bio", "abstract"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    filter_horizontal = ["topics"]
    # form
    raw_id_fields = ["session", "subsession"]
    fieldsets = [
        (None, {"fields": ["event", "code", "title", "speaker"]}),
        ("Content", {"fields": ["bio", "abstract"]}),
        ("Assignment", {"fields": ["session", "subsession", "topics"]}),
        ("Advanced", {"fields": ["extra_data"], "classes": ["collapse"]}),
        ("System", {"fields": ["uuid", "created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("event", "session", "subsession")

from django.contrib import admin

from evan.models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "key")
    list_filter = ("event",)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("key", "notes")
        return ()

from django.contrib import admin

from evan.models import Abstract


@admin.register(Abstract)
class AbstractAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user")
    list_filter = ("event",)

from django.contrib import admin

from evan.models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    pass

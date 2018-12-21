from django.contrib import admin

from evan.models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    pass

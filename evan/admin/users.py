from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from evan.models.users import User


@admin.register(User)
class UserAdmin(AuthUserAdmin):
    list_display = ("id", "username", "name", "affiliation", "email")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "affiliation",
    )

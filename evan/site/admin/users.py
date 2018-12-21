from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from evan.models import Profile

admin.site.unregister(get_user_model())


class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = 'user'


@admin.register(get_user_model())
class UserAdmin(AuthUserAdmin):
    list_display = ('id', 'username', 'name', 'affiliation', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__affiliation')

    inlines = (ProfileInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

    def name(self, obj) -> str:
        return obj.profile.name

    def affiliation(self, obj) -> str:
        return obj.profile.affiliation

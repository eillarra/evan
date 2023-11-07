from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from evan.models import Event, Fee

from .files import FilesInline
from .permissions import PermissionsInline


class FeesInline(admin.TabularInline):
    model = Fee
    classes = ("collapse",)
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = "start_date"
    list_display = (
        "code",
        "start_date",
        "end_date",
        "name",
        "sessions_link",
        "registrations_link",
        "is_active",
        "is_open",
    )
    list_per_page = 30
    search_fields = ("city", "country", "start_date__year")
    # form
    readonly_fields = ("registrations_count",)
    inlines = (
        FeesInline,
        PermissionsInline,
        FilesInline,
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).annotate(Count("sessions", distinct=True))
        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():
            return qs
        if request.user.groups.filter(name="Administration").exists():
            return qs.filter(acl__user_id__exact=request.user.id)
        return qs.none()

    # custom fields

    def is_active(self, obj) -> bool:
        return obj.is_active

    def is_open(self, obj) -> bool:
        return obj.is_open_for_registration

    def registrations_link(self, obj):
        if obj.registrations_count == 0:
            return "-"
        url = reverse("admin:evan_registration_changelist")
        return format_html(f'<a href="{url}?event__id__exact={obj.id}">{obj.registrations_count}</a>')

    def sessions_link(self, obj):
        if obj.sessions__count == 0:
            return "-"
        url = reverse("admin:evan_session_changelist")
        return format_html(f'<a href="{url}?event__id__exact={obj.id}">{obj.sessions__count}</a>')

    is_active.boolean = True
    is_active.short_description = "Active"
    is_open.boolean = True
    is_open.short_description = "Open"
    registrations_link.short_description = "Registrations"
    sessions_link.short_description = "Sessions"

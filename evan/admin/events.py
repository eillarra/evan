from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from evan.models import Event, Fee

from .rel.files import FilesInline
from .rel.links import LinksInline
from .rel.permissions import PermissionsInline


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
        LinksInline,
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

    @admin.display(description="Active", boolean=True)
    def is_active(self, obj) -> bool:
        return obj.is_active

    @admin.display(description="Open", boolean=True)
    def is_open(self, obj) -> bool:
        return obj.is_open_for_registration

    @admin.display(description="Registrations")
    def registrations_link(self, obj):
        if obj.registrations_count == 0:
            return "-"
        url = reverse("admin:evan_registration_changelist")
        return format_html(f'<a href="{url}?event__id__exact={obj.id}">{obj.registrations_count}</a>')

    @admin.display(description="Sessions")
    def sessions_link(self, obj):
        if obj.sessions__count == 0:
            return "-"
        url = reverse("admin:evan_session_changelist")
        return format_html(f'<a href="{url}?event__id__exact={obj.id}">{obj.sessions__count}</a>')

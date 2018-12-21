from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from evan.models import Event, Fee
from .generic import PermissionsInline


class FeesInline(admin.TabularInline):
    model = Fee
    classes = ('collapse',)
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    list_display = ('code', 'start_date', 'end_date', 'name', 'sessions_link', 'registrations_link',
                    'is_active', 'is_open')
    list_per_page = 30
    search_fields = ('city', 'country', 'start_date__year')

    # readonly_fields = ('registrations_count',)
    inlines = (FeesInline, PermissionsInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(Count('sessions', distinct=True)) \
                                            .annotate(Count('registrations', distinct=True))

    def is_active(self, obj) -> bool:
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'

    def is_open(self, obj) -> bool:
        return obj.is_open_for_registration
    is_open.boolean = True
    is_open.short_description = 'Open'

    def registrations_link(self, obj):
        if obj.registrations__count == 0:
            return '-'
        url = reverse('admin:evan_registration_changelist')
        return mark_safe(f'<a href="{url}?event__id__exact={obj.id}">{obj.registrations__count}</a>')
    registrations_link.short_description = 'Registrations'

    def sessions_link(self, obj):
        if obj.sessions__count == 0:
            return '-'
        url = reverse('admin:evan_session_changelist')
        return mark_safe(f'<a href="{url}?event__id__exact={obj.id}">{obj.sessions__count}</a>')
    sessions_link.short_description = 'Sessions'

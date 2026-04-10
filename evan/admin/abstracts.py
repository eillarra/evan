from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from evan.models import Abstract

from .files import FilesInline


@admin.register(Abstract)
class AbstractAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = ("id", "title", "name", "is_accepted")
    list_filter = ("is_accepted", ("event", admin.RelatedOnlyFieldListFilter))
    search_fields = ("id", "uuid", "user__email", "user__username", "user__first_name", "user__last_name", "title")
    # form
    raw_id_fields = ("event", "user")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("is_accepted", "event", "user", "created_at", "updated_at"),
            },
        ),
        (
            "Abstract",
            {
                "fields": (
                    "title",
                    "authors",
                    "abstract",
                    "custom_data",
                ),
            },
        ),
    )
    inlines = (FilesInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user").prefetch_related("event")
        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():
            return qs
        if request.user.groups.filter(name="Abstract management").exists():
            return qs.filter(event__acl__user_id__exact=request.user.id)
        return qs.none()

    def name(self, obj):
        affiliation = obj.user.affiliation if obj.user.affiliation else "-"
        url = reverse("admin:auth_user_changelist")
        return format_html(
            '<a href="{}{}" target="admin_user">{}</a>, {}', url, obj.user_id, obj.user.name, affiliation
        )

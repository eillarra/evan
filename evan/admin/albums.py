from django.contrib import admin

from evan.models import Album

from .rel.files import FilesInline


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "files_count")
    list_filter = ("event",)
    search_fields = ("title", "event__name", "event__code")
    readonly_fields = ("files_count",)
    inlines = (FilesInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("event").prefetch_related("files")

        if request.user.is_superuser or request.user.groups.filter(name="Management").exists():  # type: ignore
            return qs
        if request.user.groups.filter(name="Administration").exists():  # type: ignore
            return qs.filter(event__acl__user_id__exact=request.user.id)  # type: ignore
        return qs.none()

    @admin.display(description="Files")
    def files_count(self, obj):
        return obj.files.count()

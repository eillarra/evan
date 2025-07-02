from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from requests.exceptions import HTTPError

from evan.models.rel.files import File
from evan.services.s3 import get_s3_response


class MediaFileView(View):
    """
    Serves private S3 files, checking user permissions beforehand if needed.
    """

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().is_accessible_by_user(request.user):  # type: ignore
            raise PermissionDenied("You don't have the necessary permissions to access this file.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self) -> File:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(File, file=self.request.path.replace("/media/", "", 1))
        return self.object

    def get(self, request, *args, **kwargs):
        file = self.get_object()

        try:
            res = get_s3_response(file.s3_object_key)
        except HTTPError as exc:
            raise Http404("File not found.") from exc

        # Determine cache behavior based on file visibility
        cache_control = "public, max-age=3600" if file.is_public else "private, no-cache"

        response = HttpResponse(
            res.raw,
            headers={
                "Content-Disposition": f'inline; filename="{file.file.name}"',
                "Content-Length": res.headers["Content-Length"],
                "Content-Type": res.headers["Content-Type"],
                "Cache-Control": cache_control,
            },
        )

        # Mark response to prevent middleware from adding cookies
        response._no_cookies = True  # type: ignore

        return response

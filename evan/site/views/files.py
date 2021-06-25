import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from mimetypes import guess_type

from evan.models import File


class SendfileView(View):
    """
    Serves `private` assets.
    """

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(File, file=self.request.path.replace("/media/", ""))
        return self.object

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        full_path = obj.file.name.replace("private", "", 1)
        response = HttpResponse()

        url = f"{settings.SENDFILE_URL}{full_path}"
        guessed_mimetype, guessed_encoding = guess_type(kwargs.get("filename"))

        response["X-Accel-Redirect"] = url.encode("utf-8")
        response["Content-Type"] = guessed_mimetype if guessed_mimetype else "application/octet-stream"
        response["Content-length"] = os.path.getsize(f"{settings.SENDFILE_ROOT}{full_path}")
        if guessed_encoding:
            response["Content-Encoding"] = guessed_encoding

        return response


class PrivateFileView(SendfileView):
    """
    Serves `private` files, checking basic permissions beforehand.
    """

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            raise PermissionDenied
        if not self.get_object().content_object.viewable_by_user(self.request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

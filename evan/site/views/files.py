from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views.generic import View
from requests.exceptions import HTTPError

from evan.models.rel.files import File
from evan.services.file_guard import get_presented_secret
from evan.services.s3 import get_s3_response


# Keys uploaded before the visibility tiers existed, see the relocate_files command.
LEGACY_KEY_PREFIXES = ("public/", "private/")


def get_relocated_key(key: str) -> str | None:
    """Return the visibility-free key a legacy visibility-prefixed key moved to.

    :param key: The stored name taken from the request path.
    :returns: The key the file now uses, or None if the key is not a legacy one.
    """
    for prefix in LEGACY_KEY_PREFIXES:
        if key.startswith(prefix):
            return f"files/{key.removeprefix(prefix)}"
    return None


class MediaFileView(View):
    """
    Serves files, checking the file guard beforehand if needed.

    The file's visibility tier decides the audience: public files are open to
    everyone, the other tiers are served to the people the guard accepts. The
    owning object's secret, presented in the ``X-Evan-Secret`` header, unlocks
    that object's own files when the object accepts it — the session, whose
    secret link is the session organizer's way in.

    Files are looked up by their stored name, which the relocation command
    rewrites; the pre-relocation addresses are still resolved to the moved
    object so the links already handed out keep working. That fallback goes away
    with the command.
    """

    def dispatch(self, request, *args, **kwargs):
        file = self.get_object()
        secret = get_presented_secret(request)

        # A login_required decorator cannot be used here: the same URL serves
        # public and non-public files, so the redirect must happen per file after
        # the lookup, never for public files.
        if not file.is_public and not request.user.is_authenticated and not secret:  # type: ignore
            return redirect_to_login(next=request.get_full_path())

        if not file.is_accessible_by_user(request.user, secret=secret):  # type: ignore
            raise PermissionDenied("You don't have the necessary permissions to access this file.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self) -> File:
        """Resolve the file the request path names.

        :returns: The file stored at that address.
        :raises Http404: If no file is stored there.
        """
        if not hasattr(self, "object"):
            key = self.request.path.replace("/media/", "", 1)
            file = File.objects.filter(file=key).first()

            if file is None:
                relocated_key = get_relocated_key(key)
                if relocated_key:
                    file = File.objects.filter(file=relocated_key).first()

            if file is None:
                raise Http404("File not found.")

            self.object = file
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

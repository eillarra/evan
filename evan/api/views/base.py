from http import HTTPStatus as status

from django.db.models.deletion import ProtectedError
from rest_framework.response import Response


class ProtectedMixin:
    """Mixin to handle protected objects."""

    def destroy(self, request, *args, **kwargs):
        """Try destroying a model instance.

        If `PROTECT` has been set as `on_delete` for a foreign key,return a `403 Forbidden` response.
        """
        try:
            return super().destroy(request, *args, **kwargs)  # type: ignore
        except ProtectedError as e:
            message, _ = e.args
            return Response({"protected": [message]}, status=status.FORBIDDEN)

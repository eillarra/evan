import hmac
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from evan import models


def check_file_access(
    file: models.rel.File,
    user: models.User | AbstractBaseUser | AnonymousUser,
    secret: str | None = None,
) -> bool:
    """
    Check if a user has access to a file.

    This is done in one place to have a better overview of the access control for
    non-public files. The access rules themselves live on the content object's
    model: every model using the files mixin provides ``files_viewable_by_user``
    (with model-specific overrides such as Album excluding no-shows) and
    ``files_can_be_managed_by``.

    The file's visibility tier selects the rule:

    - ``public``: everyone, including anonymous visitors;
    - ``attendees``: those who may view the owning object;
    - ``organizers``: those who may manage the owning object.

    A requester presenting the owning object's secret is treated as that
    object's organizer, whatever the tier — only for the objects that opt in
    on ``FilesMixin.files_secret_unlocks`` (today: the session, whose secret
    link is the session organizer's way in).

    :param file: The file to check access for
    :param user: The user to check access for
    :param secret: An optional secret of the owning object
    :returns: True if the user has access to the file
    :raises NotImplementedError if the file's content object has no access control
    """

    if file.visibility == file.PUBLIC:
        return True

    if not user.is_authenticated and not secret:
        return False

    if secret and has_matching_secret(file.content_object, secret):  # type: ignore[arg-type]
        return True

    if not user.is_authenticated:
        return False

    if file.visibility == file.ORGANIZERS:
        return file.content_object.files_can_be_managed_by(user)  # type: ignore[union-attr]

    return file.content_object.files_viewable_by_user(user)  # type: ignore[union-attr]


def get_presented_secret(request: Any) -> str | None:
    """Return the secret presented by the request, if any.

    The secret travels in a header so it never lands in access logs or in the
    ``Referer`` of any outbound link.

    :param request: The incoming request, Django or DRF.
    :returns: The presented secret, or None.
    """
    if request is None:
        return None
    return request.headers.get("X-Evan-Secret")


def has_matching_secret(content_object: models.Model | None, secret: str | None) -> bool:
    """Check whether the secret belongs to the given content object.

    Only objects that opt in on ``FilesMixin.files_secret_unlocks`` accept
    their own secret as a management credential; the check is opt-in rather
    than derived from the presence of a ``secret`` attribute because several
    objects carry a secret for an unrelated purpose (a registration's
    delegated-payment link, a paper's or keynote's editing link). The secret is
    only ever accepted for the object it was issued for.

    :param content_object: The object owning the file.
    :param secret: The secret presented by the requester.
    :returns: True if the secret matches the object's own secret.
    """
    if not secret or not getattr(content_object, "files_secret_unlocks", False):
        return False

    object_secret = getattr(content_object, "secret", None)
    if not object_secret:
        return False

    # Compared as bytes: ``compare_digest`` rejects non-ASCII str values, and a
    # header is decoded latin-1, so a crafted secret would otherwise raise.
    return hmac.compare_digest(str(object_secret).encode(), str(secret).encode())

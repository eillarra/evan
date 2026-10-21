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
    object's organizer, whatever the tier.

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


def has_matching_secret(content_object, secret: str) -> bool:
    """Check whether the secret belongs to the given content object.

    Only objects that expose a secret (sessions, subsessions, papers, keynotes)
    can be unlocked this way, and the secret is only ever accepted for the
    object it was issued for.

    :param content_object: The object owning the file.
    :param secret: The secret presented by the requester.
    :returns: True if the secret matches the object's own secret.
    """
    object_secret = getattr(content_object, "secret", None)
    if not object_secret:
        return False
    return str(object_secret) == secret

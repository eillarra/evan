from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from evan import models


def check_file_access(file: models.rel.File, user: models.User | AbstractBaseUser | AnonymousUser) -> bool:
    """
    Check if a user has access to a file.
    This is done in one place to have a better overview of the access control for private files.

    The access rules themselves live on the content object's model: every
    model using the files mixin provides ``files_viewable_by_user`` (with
    model-specific overrides such as Album excluding no-shows).

    :param file: The file to check access for
    :param user: The user to check access for
    :returns: True if the user has access to the file
    :raises: NotImplementedError if the file's content object has no access control
    """

    if not user.is_authenticated:
        return False

    return file.content_object.files_viewable_by_user(user)  # type: ignore[union-attr]

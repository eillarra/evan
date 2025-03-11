from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from evan import models


def check_file_access(file: "models.rel.File", user: "models.User | AbstractBaseUser | AnonymousUser") -> bool:
    """
    Check if a user has access to a file.
    This is done in one place to have a better overview of the access control for private files.

    :param file: The file to check access for
    :param user: The user to check access for
    :return: True if the user has access to the file
    :raises: NotImplementedError if no access control is implemented for the file's content object
    """

    if not user.is_authenticated:
        return False

    return file.content_object.files_can_be_managed_by(user)  # type: ignore[union-attr]

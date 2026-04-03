from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from evan import models


def check_file_access(file: models.rel.File, user: models.User | AbstractBaseUser | AnonymousUser) -> bool:
    """
    Check if a user has access to a file.
    This is done in one place to have a better overview of the access control for private files.

    :param file: The file to check access for
    :param user: The user to check access for
    :returns: True if the user has access to the file
    :raises: NotImplementedError if no access control is implemented for the file's content object
    """

    if not user.is_authenticated:
        return False

    # For album files, use the album's access control method
    if isinstance(file.content_object, models.Album):
        return file.content_object.is_accessible_by_user(user)  # type: ignore

    return file.content_object.files_can_be_managed_by(user)  # type: ignore[union-attr]

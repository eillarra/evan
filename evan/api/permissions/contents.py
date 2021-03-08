from .events import EventRelatedObjectPermission


class ContentPermission(EventRelatedObjectPermission):
    allow_delete = False

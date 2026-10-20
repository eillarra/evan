from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from evan.models import Registration
from evan.models.rel.remarks import RemarksMixin

from ...serializers.rel.remarks import RemarkSerializer
from .base import RelModelViewSet


class RemarkPermission(IsAuthenticated):
    """Remarks are private notes: only the managers of the event an object belongs to may read or write them.

    Managers are defined as for the related files: platform staff, and users with an administrator or owner
    access row on the event.
    """

    def has_permission(self, request: Request, view: RelModelViewSet) -> bool:
        """Check that the user manages the event of the object the remarks belong to.

        :param request: The incoming request.
        :param view: The remarks view, which resolves the parent object from the URL.
        :returns: Whether the user may access the remarks of that object.
        """
        if not super().has_permission(request, view):
            return False

        parent = self.get_parent(view)
        # Only registrations carry the event that managers are checked against; other parents are refused.
        return isinstance(parent, Registration) and parent.event.can_be_managed_by(request.user)

    @staticmethod
    def get_parent(view: RelModelViewSet) -> RemarksMixin | None:
        """Resolve the object named in the URL, if it exists and can carry remarks.

        :param view: The remarks view, which resolves the parent object from the URL.
        :returns: The parent, or None for an unknown object or for a model that cannot carry remarks.
        """
        try:
            model = ContentType.objects.get_for_id(int(view.kwargs["parent_lookup_content_type_id"])).model_class()
            return view.get_content_object() if model and issubclass(model, RemarksMixin) else None
        except ObjectDoesNotExist, ValueError:
            return None


class RemarkViewSet(RelModelViewSet):
    auto_created_by = True
    pagination_class = None
    permission_classes = [RemarkPermission]
    serializer_class = RemarkSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return self.get_content_object().remarks.select_related("created_by")  # type: ignore

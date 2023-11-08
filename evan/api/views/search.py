from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models.users import User

from ..permissions import EventManagerPermission
from ..serializers import UserTinySerializer


class UserSearchViewSet(ListModelMixin, GenericViewSet):
    permission_classes = (EventManagerPermission,)
    queryset = User.objects.only("id", "email", "first_name", "last_name")
    filter_backends = (SearchFilter,)
    search_fields = ("username", "email", "first_name", "last_name")
    serializer_class = UserTinySerializer

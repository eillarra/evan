from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from ..permissions import EventManagerPermission
from ..serializers import UserBasicSerializer


class UserSearchViewSet(ListModelMixin, GenericViewSet):
    permission_classes = (EventManagerPermission,)
    queryset = get_user_model().objects.only("id", "email", "first_name", "last_name")
    filter_backends = (SearchFilter,)
    search_fields = ("username", "email", "first_name", "last_name")
    serializer_class = UserBasicSerializer

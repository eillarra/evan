from django.contrib.auth import get_user_model
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from ..permissions import UserPermission
from ..serializers import UserSerializer


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = 'username'
    permission_classes = (UserPermission,)
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer

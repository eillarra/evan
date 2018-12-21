from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from ..permissions import UserPermission
from ..serializers import UserSerializer


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = (UserPermission,)
    queryset = get_user_model().objects.select_related('profile')
    serializer_class = UserSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

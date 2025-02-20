from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Permission, Registration, User

from ..permissions import UserPermission
from ..serializers import AuthRegistrationRetrieveSerializer, EventListSerializer, UserSerializer


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = (UserPermission,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, pagination_class=None, serializer_class=EventListSerializer)
    @method_decorator(never_cache)
    def events(self, request, *args, **kwargs):
        self.queryset = Event.objects.filter(acl__user_id=request.user.id, acl__level__gte=Permission.ADMIN)
        return ListModelMixin.list(self, request, *args, **kwargs)

    @action(detail=False, pagination_class=None, serializer_class=AuthRegistrationRetrieveSerializer)
    @method_decorator(never_cache)
    def registrations(self, request, *args, **kwargs):
        self.queryset = Registration.objects.filter(user_id=request.user.id)
        return ListModelMixin.list(self, request, *args, **kwargs)

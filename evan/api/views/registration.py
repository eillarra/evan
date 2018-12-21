from django.db import IntegrityError
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Coupon, Registration
from ..permissions import EventRelatedObjectPermission, RegistrationPermission
from ..serializers import CouponSerializer, RegistrationSerializer, RegistrationRetrieveSerializer
from ..viewsets import EventRelatedViewSet


class CouponsViewSet(EventRelatedViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class CouponViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class RegistrationsViewSet(EventRelatedViewSet):
    queryset = Registration.objects.select_related('user__profile').prefetch_related('coupon')
    serializer_class = RegistrationRetrieveSerializer

    def list(self, request, *args, **kwargs):
        self.serializer_class = RegistrationSerializer
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, event=Event.objects.get(code=self.kwargs.get('code')))
        except IntegrityError:
            raise ValidationError({'event-user': ['Duplicate entry - this user already has a registration.']})


class RegistrationCreateViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Registration.objects.select_related('user__profile').prefetch_related('coupon')
    serializer_class = RegistrationRetrieveSerializer

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, event=Event.objects.get(code=self.kwargs.get('code')))
        except IntegrityError:
            raise ValidationError({'event-user': ['Duplicate entry - this user already has a registration.']})


class RegistrationViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    permission_classes = (RegistrationPermission,)
    queryset = Registration.objects.prefetch_related('sessions').select_related('user__profile')
    serializer_class = RegistrationRetrieveSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

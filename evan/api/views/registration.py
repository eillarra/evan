from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.decorators import detail_route
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from evan.models import Coupon, Registration
# from evan.services.stripe import create_charge
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
    queryset = Registration.objects.select_related('user__profile')
    serializer_class = RegistrationSerializer


class RegistrationViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    permission_classes = (RegistrationPermission,)
    queryset = Registration.objects.prefetch_related('sessions').select_related('user__profile')
    serializer_class = RegistrationRetrieveSerializer

    @never_cache
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @detail_route(methods=['post'])
    @never_cache
    def charge(self, request, *args, **kwargs):
        registration = self.get_object()

        if registration.is_paid or request.data['amount'] > -registration.saldo:
            raise serializers.ValidationError({'payment': ['Not processed: your registration has already been paid.']})

        try:
            # create_charge(registration, request.data['amount'], request.data['token'])
            return Response(RegistrationRetrieveSerializer(self.get_object()).data)
        except Exception as e:
            raise serializers.ValidationError({'payment': [str(e)]})

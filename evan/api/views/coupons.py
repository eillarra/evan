from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Coupon

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import CouponSerializer
from ..viewsets import EventRelatedViewSet
from .base import ProtectedMixin


class CouponsPermission(EventRelatedPermission):
    allow_list_to_all = False
    allow_create_to_manager = True


class CouponPermission(EventRelatedObjectPermission):
    allow_update_to_manager = True
    allow_delete_to_manager = True


class CouponsViewSet(EventRelatedViewSet):
    permission_classes = [CouponsPermission]
    queryset = Coupon.objects.order_by("notes").all()
    serializer_class = CouponSerializer


class CouponViewSet(ProtectedMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [CouponPermission]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

from rest_framework import serializers
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Room, Venue

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers import RoomSerializer, VenueSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet, EventRelatedViewSet


class VenuesPermission(EventRelatedPermission):
    allow_list_to_all = False
    allow_create_to_manager = True


class VenuePermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = False
    allow_update_to_manager = True
    allow_delete_to_manager = True


class RoomsPermission(EventRelatedPermission):
    allow_create_to_manager = True


class RoomPermission(EventRelatedObjectPermission):
    allow_retrieve_to_all = False
    allow_update_to_manager = True
    allow_delete_to_manager = True

    def get_event_id(self, obj):
        return obj.venue.event_id


class VenuesViewSet(EventRelatedViewSet):
    permission_classes = [VenuesPermission]
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer


class VenueViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (VenuePermission,)
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer


class RoomsViewSet(EventRelatedCreateOnlyViewSet):
    permission_classes = [RoomsPermission]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def create(self, request, *args, **kwargs):
        if not Venue.objects.filter(id=request.data.get("venue"), event__code=kwargs.get("code")).exists():
            raise serializers.ValidationError({"venue": ["Venue is not valid for this event."]})
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class RoomViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (RoomPermission,)
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

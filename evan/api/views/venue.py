from rest_framework import serializers
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from evan.models import Venue, Room
from ..permissions import EventRelatedObjectPermission, RoomPermission
from ..serializers import VenueSerializer, RoomSerializer
from ..viewsets import EventRelatedCreateOnlyViewSet


class RoomsViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def create(self, request, *args, **kwargs):
        if not Venue.objects.filter(id=request.data.get("venue"), event__code=kwargs.get("code")).exists():
            raise serializers.ValidationError({"venue": ["Venue is not valid for this event."]})
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class RoomViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (RoomPermission,)
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class VenuesViewSet(EventRelatedCreateOnlyViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer


class VenueViewSet(UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (EventRelatedObjectPermission,)
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer

from rest_framework import status
from rest_framework.test import APITestCase

from toucon.models import Conference, Venue
from toucon.api.serializers import VenueSerializer, RoomSerializer
from .conference import ConferenceTests


class VenueTests(APITestCase):
    def setUp(self):
        ConferenceTests.setUp(self)
        self.venue1 = Venue.objects.create(name='venue1', conference=self.conference)
        self.venue2 = Venue.objects.create(name='venue2', conference=self.conference)

    def test_venue_serializer():
        serializer = VenueSerializer()
        f = serializer.fields['field_name']
        obj = Venue()

        assert f.to_representation(obj) == '0.00'
        obj.prop = 123
        assert f.to_representation(obj) == '1.23'

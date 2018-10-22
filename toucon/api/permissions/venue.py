from .conference import ConferenceRelatedObjectPermission


class RoomPermission(ConferenceRelatedObjectPermission):
    def get_conference_id(self, obj):
        return obj.venue.conference_id

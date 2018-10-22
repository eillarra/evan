from .event import EventRelatedObjectPermission


class RoomPermission(EventRelatedObjectPermission):

    def get_event_id(self, obj):
        return obj.venue.event_id

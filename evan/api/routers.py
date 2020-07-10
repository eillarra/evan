from rest_framework.routers import DefaultRouter

from evan.api import views


class Router(DefaultRouter):
    def __init__(self, version="v1"):
        super().__init__()

        self.schema_title = "Evan API {0}".format(version)

        self.register(r"metadata", views.MetadataViewSet, basename="metadata")
        self.register(r"users", views.UserViewSet, basename="user")

        self.register(r"events", views.EventViewSet, basename="event")
        self.register(r"events/(?P<code>[\w-]+)/contents", views.ContentsViewSet, basename="contents")
        self.register(r"events/(?P<code>[\w-]+)/coupons", views.CouponsViewSet, basename="coupons")
        self.register(r"events/(?P<code>[\w-]+)/papers", views.PapersViewSet, basename="papers")
        self.register(r"events/(?P<code>[\w-]+)/registrations", views.RegistrationsViewSet, basename="registrations")
        self.register(r"events/(?P<code>[\w-]+)/rooms", views.RoomsViewSet, basename="rooms")
        self.register(r"events/(?P<code>[\w-]+)/sessions", views.SessionsViewSet, basename="sessions")
        self.register(r"events/(?P<code>[\w-]+)/topics", views.TopicsViewSet, basename="topics")
        self.register(r"events/(?P<code>[\w-]+)/tracks", views.TracksViewSet, basename="tracks")
        self.register(r"events/(?P<code>[\w-]+)/venues", views.VenuesViewSet, basename="venues")

        self.register(r"events/(?P<code>[\w-]+)/register", views.RegistrationCreateViewSet, basename="register")

        self.register(r"coupons", views.CouponViewSet, basename="coupon")
        self.register(r"papers", views.PaperViewSet, basename="paper")
        self.register(r"registrations", views.RegistrationViewSet, basename="registration")
        self.register(r"rooms", views.RoomViewSet, basename="room")
        self.register(r"sessions", views.SessionViewSet, basename="session")
        self.register(r"topics", views.TopicViewSet, basename="topic")
        self.register(r"tracks", views.TrackViewSet, basename="track")
        self.register(r"venues", views.VenueViewSet, basename="venue")

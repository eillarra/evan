from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet
from rest_framework_extensions.routers import NestedRouterMixin

from evan.api import views


class DummyViewSet(ViewSet):
    """Dummy viewset to register nested routes."""

    pass


class Router(NestedRouterMixin, DefaultRouter):
    """Router for Evan API."""

    def __init__(self, version="v1"):
        super().__init__()

        self.schema_title = f"Evan API {version}"

        # /users/

        self.register(r"user", views.UserViewSet, basename="user")

        # /rel/{parent_lookup_content_type_id}/{parent_lookup_object_id}/remarks/

        rel_routes_pql = ["content_type_id", "object_id"]
        rel_routes = self.register(r"rel/(?P<parent_lookup_content_type_id>\d+)", DummyViewSet, basename="rel")
        rel_routes.register("files", views.FileViewSet, basename="file", parents_query_lookups=rel_routes_pql)
        rel_routes.register("remarks", views.RemarkViewSet, basename="remark", parents_query_lookups=rel_routes_pql)

        # /events/

        self.register(r"events", views.EventViewSet, basename="event")
        self.register(r"events/(?P<code>[\w-]+)/abstracts", views.AbstractsViewSet, basename="abstracts")
        self.register(r"events/(?P<code>[\w-]+)/contents", views.ContentsViewSet, basename="contents")
        self.register(r"events/(?P<code>[\w-]+)/coupons", views.CouponsViewSet, basename="coupons")
        self.register(r"events/(?P<code>[\w-]+)/emails", views.EmailsViewSet, basename="emails")
        self.register(r"events/(?P<code>[\w-]+)/papers", views.PapersViewSet, basename="papers")
        self.register(r"events/(?P<code>[\w-]+)/registrations", views.RegistrationsViewSet, basename="registrations")
        self.register(r"events/(?P<code>[\w-]+)/reviews", views.AbstractReviewsViewSet, basename="reviews")
        self.register(r"events/(?P<code>[\w-]+)/rooms", views.RoomsViewSet, basename="rooms")
        self.register(r"events/(?P<code>[\w-]+)/sessions", views.SessionsViewSet, basename="sessions")
        self.register(r"events/(?P<code>[\w-]+)/sponsors", views.SponsorsViewSet, basename="sponsors")
        self.register(r"events/(?P<code>[\w-]+)/topics", views.TopicsViewSet, basename="topics")
        self.register(r"events/(?P<code>[\w-]+)/tracks", views.TracksViewSet, basename="tracks")
        self.register(r"events/(?P<code>[\w-]+)/venues", views.VenuesViewSet, basename="venues")

        self.register(r"events/(?P<code>[\w-]+)/abstract", views.AbstractCreateViewSet, basename="submit_abstract")
        self.register(r"events/(?P<code>[\w-]+)/register", views.RegistrationCreateViewSet, basename="register")
        self.register(r"events/(?P<code>[\w-]+)/review", views.AbstractReviewCreateViewSet, basename="create_review")

        # view routes

        self.register(r"abstracts", views.AbstractViewSet, basename="abstract")
        self.register(r"contents", views.ContentViewSet, basename="content")
        self.register(r"coupons", views.CouponViewSet, basename="coupon")
        self.register(r"emails", views.EmailViewSet, basename="email")
        self.register(r"papers", views.PaperViewSet, basename="paper")
        self.register(r"registrations", views.RegistrationViewSet, basename="registration")
        self.register(r"reviews", views.AbstractReviewViewSet, basename="review")
        self.register(r"rooms", views.RoomViewSet, basename="room")
        self.register(r"sessions", views.SessionViewSet, basename="session")
        self.register(r"sponsors", views.SponsorViewSet, basename="sponsor")
        self.register(r"topics", views.TopicViewSet, basename="topic")
        self.register(r"tracks", views.TrackViewSet, basename="track")
        self.register(r"venues", views.VenueViewSet, basename="venue")

        self.register(r"search/users", views.UserSearchViewSet, basename="search_users")

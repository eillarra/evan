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

        # /rel/{parent_lookup_content_type_id}/{parent_lookup_object_id}/**/

        rel_routes_pql = ["content_type_id", "object_id"]
        rel_routes = self.register(r"rel/(?P<parent_lookup_content_type_id>\d+)", DummyViewSet, basename="rel")
        rel_routes.register("files", views.FileViewSet, basename="file", parents_query_lookups=rel_routes_pql)
        rel_routes.register("remarks", views.RemarkViewSet, basename="remark", parents_query_lookups=rel_routes_pql)

        # /events/**/

        self.register(r"events", views.EventViewSet, basename="event")
        self.register(r"events/(?P<code>[\w-]+)/abstracts", views.AbstractsViewSet, basename="abstracts")
        self.register(r"events/(?P<code>[\w-]+)/albums", views.AlbumsViewSet, basename="albums")
        self.register(r"events/(?P<code>[\w-]+)/contents", views.ContentsViewSet, basename="contents")
        self.register(r"events/(?P<code>[\w-]+)/coupons", views.CouponsViewSet, basename="coupons")
        self.register(r"events/(?P<code>[\w-]+)/emails", views.EmailsViewSet, basename="emails")
        self.register(r"events/(?P<code>[\w-]+)/emailplans", views.EmailPlansViewSet, basename="emailplans")
        self.register(r"events/(?P<code>[\w-]+)/keynotes", views.KeynotesViewSet, basename="keynotes")
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

        self.register("abstracts", views.AbstractViewSet, basename="abstract")
        self.register("albums", views.AlbumViewSet, basename="album")
        self.register("contents", views.ContentViewSet, basename="content")
        self.register("coupons", views.CouponViewSet, basename="coupon")
        self.register("emails", views.EmailViewSet, basename="email")
        self.register("emailplans", views.EmailPlanViewSet, basename="emailplan")
        self.register("keynotes", views.KeynoteViewSet, basename="keynote")
        self.register("papers", views.PaperViewSet, basename="paper")
        self.register("registrations", views.RegistrationViewSet, basename="registration")
        self.register("reviews", views.AbstractReviewViewSet, basename="review")
        self.register("rooms", views.RoomViewSet, basename="room")

        sessions_routes = self.register(r"sessions", views.SessionViewSet, basename="session")
        sessions_routes.register(
            "subsessions",
            views.SubsessionsViewSet,
            basename="session-subsessions",
            parents_query_lookups=["session_id"],
        )

        self.register("sponsors", views.SponsorViewSet, basename="sponsor")
        self.register("subsessions", views.SubsessionViewSet, basename="subsession")
        self.register("topics", views.TopicViewSet, basename="topic")
        self.register("tracks", views.TrackViewSet, basename="track")
        self.register("venues", views.VenueViewSet, basename="venue")

        self.register("search/users", views.UserSearchViewSet, basename="search_users")

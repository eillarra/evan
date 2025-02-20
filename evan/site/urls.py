from django.conf.urls import include
from django.urls import path
from django.views.decorators.cache import never_cache

from evan.site import views
from evan.site.views.events import EventView


event_patterns = (
    [
        path(
            "<slug:code>/",
            include(
                [
                    path("", EventView.as_view(), name="app"),
                    # path("files/badges.pdf", views.EventBadgesPdf.as_view(), name="badges"),
                    # path("files/abstracts.xlsx", views.EventAbstractsSheet.as_view(), name="abstracts_sheet"),
                    # path("files/registrations.xlsx", views.EventRegistrationsSheet.as_view(), name="registrations_sheet"),
                ]
            ),
        ),
    ],
    "event_patterns",
)

registration_patterns = (
    [
        path("<slug:code>/", views.RegistrationView.as_view(), name="app"),
        path(
            "<uuid:uuid>/",
            include(
                [
                    path("certificate.pdf", never_cache(views.EventView.as_view()), name="certificate"),
                    path("payment/", never_cache(views.EventView.as_view()), name="payment"),
                    path("receipt.pdf", never_cache(views.EventView.as_view()), name="receipt"),
                ]
            ),
        ),
    ],
    "registration_patterns",
)

session_patterns = (
    [
        path("<uuid:uuid>/<slug:secret>/", views.SessionSecretEditorView.as_view(), name="secret"),
    ],
    "session_patterns",
)

urlpatterns = [
    path("", views.HomeView.as_view(), name="homepage"),
    path("u/dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("e/", include(event_patterns, namespace="event")),
    path("r/", include(registration_patterns, namespace="registration")),
    path("s/", include(session_patterns, namespace="session")),
]

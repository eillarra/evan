from django.conf.urls import include
from django.urls import path
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from evan.site import views
from evan.site.views.events import EventView


event_patterns = (
    [
        path(
            "<slug:code>/",
            include(
                [
                    path("", EventView.as_view(), name="app"),
                    path("files/badges.pdf", views.EventBadgesPdf.as_view(), name="badges"),
                    # path("files/abstracts.xlsx", views.EventAbstractsSheet.as_view(), name="abstracts_sheet"),
                    path("files/<slug:file_code>.xlsx", views.EventExcelView.as_view(), name="event_excel"),
                    path(
                        "registration-preview/",
                        views.EventRegistrationPreviewView.as_view(),
                        name="registration_preview",
                    ),
                ]
            ),
        ),
    ],
    "event_patterns",
)

paper_patterns = (
    [
        path("<uuid:uuid>/<slug:secret>/", views.PaperSecretEditorView.as_view(), name="secret"),
    ],
    "paper_patterns",
)

registration_patterns = (
    [
        path(
            "<uuid:uuid>/",
            include(
                [
                    path("", views.RegistrationRedirectView.as_view(), name="registration_redirect"),
                    path(
                        "certificate.pdf", never_cache(views.RegistrationCertificatePdf.as_view()), name="certificate"
                    ),
                    path("payment/", never_cache(views.RegistrationPaymentView.as_view()), name="payment"),
                    path(
                        "payment/callback/",
                        never_cache(views.RegistrationPaymentResultView.as_view()),
                        name="payment_callback",
                    ),
                    path(
                        "payment/result/",
                        never_cache(views.RegistrationPaymentResultView.as_view()),
                        name="payment_result",
                    ),
                    path("receipt.pdf", never_cache(views.RegistrationReceiptPdf.as_view()), name="receipt"),
                    path(
                        "invoice-request/",
                        never_cache(views.RegistrationInvoiceRequestView.as_view()),
                        name="invoice_request",
                    ),
                ]
            ),
        ),
        path(
            "<uuid:uuid>/d/p/<slug:secret>/",
            include(
                [
                    path("", never_cache(views.RegistrationPaymentDelegatedView.as_view()), name="payment_delegated"),
                    path(
                        "result/",
                        never_cache(views.RegistrationPaymentDelegatedResultView.as_view()),
                        name="payment_delegated_result",
                    ),
                ]
            ),
        ),
        path("<slug:code>/", views.RegistrationView.as_view(), name="app"),
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
    path("done/", TemplateView.as_view(template_name="pages/done.html"), name="done"),
    path("u/dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("e/", include(event_patterns, namespace="event")),
    path("p/", include(paper_patterns, namespace="paper")),
    path("r/", include(registration_patterns, namespace="registration")),
    path("s/", include(session_patterns, namespace="session")),
]

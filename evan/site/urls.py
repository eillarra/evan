from django.conf.urls import include
from django.contrib.flatpages.views import flatpage
from django.urls import path, re_path
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from evan.site import views


event_patterns = (
    [
        path(
            "<slug:code>/",
            include(
                [
                    path("", views.EventView.as_view(), name="app"),
                    path("files/badges.pdf", views.EventBadgesPdf.as_view(), name="badges"),
                    path("files/overview.xlsx", views.EventSpreadsheet.as_view(), name="registrations_sheet"),
                ]
            ),
        ),
    ],
    "event_patterns",
)

registration_patterns = (
    [
        path(
            "<uuid:uuid>/",
            include(
                [
                    path("", views.RegistrationView.as_view(), name="app"),
                    path(
                        "certificate.pdf", never_cache(views.RegistrationCertificatePdf.as_view()), name="certificate"
                    ),
                    path("payment/", never_cache(views.RegistrationPaymentView.as_view()), name="payment"),
                    path(
                        "d/<slug:secret>/",
                        never_cache(views.RegistrationPaymentDelegatedView.as_view()),
                        name="payment_delegated",
                    ),
                    path(
                        "payment/result/",
                        never_cache(views.RegistrationPaymentResultView.as_view()),
                        name="payment_result",
                    ),
                    path(
                        "payment/result/d/",
                        never_cache(views.RegistrationPaymentDelegatedResultView.as_view()),
                        name="payment_delegated_result",
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
        path("<slug:code>/", views.RegistrationRedirectView.as_view(), name="redirect"),
    ],
    "registration_patterns",
)

urlpatterns = [
    path("e/", include(event_patterns, namespace="event")),
    path("r/", include(registration_patterns, namespace="registration")),
    path("u/", include("allauth.urls")),
    path("u/dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("disclaimer/", flatpage, {"url": "/disclaimer/"}, name="disclaimer"),
    path("privacy/", flatpage, {"url": "/privacy/"}, name="privacy"),
    path("terms/", flatpage, {"url": "/terms/"}, name="terms"),
    path("done/", TemplateView.as_view(template_name="pages/done.html"), name="done"),
    path("", TemplateView.as_view(template_name="pages/homepage.html"), name="homepage"),
]

# Flatpages “catchall” pattern
urlpatterns += [
    re_path(r"^(?P<url>.*/)$", flatpage),
]

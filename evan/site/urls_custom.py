from django.urls import path

from evan.site.views.custom.icoodim import IcoodimPdfBundleView


# fmt: off

custom_patterns = ([
    path("icoopma-eurodim/session-abstracts/<slug:session>.pdf", IcoodimPdfBundleView.as_view()),
], "custom_patterns")

from django.conf.urls import include
from django.urls import path
from rest_framework.documentation import include_docs_urls

from .routers import Router
from .views.countries import get_countries


urlpatterns = [
    path("countries/", get_countries, name="countries"),
    path("v1/", include((Router("v1").urls, "api"), namespace="v1")),
    path("", include_docs_urls(title="Evan API")),
]

from django.conf.urls import include
from django.urls import path

from .routers import Router
from .views.countries import get_countries


urlpatterns = [
    path("countries/", get_countries, name="countries"),
    path("v1/", include((Router("v1").urls, "api"), namespace="v1")),
]

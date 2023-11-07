from os import environ

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event
from evan.site.pdfs.badges import BadgesPdfMaker
from evan.site.sheets.abstracts import AbstractsSheet
from evan.site.sheets.registrations import RegistrationsSheet


class EventView(generic.DetailView):
    template_name = "app/events/index.html"

    def get_object(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().editable_by_user(request.user):
            messages.error(
                request,
                "You don't have the necessary permissions to manage this event.",
            )
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_maps_static_api_key"] = environ.get("GOOGLE_MAPS_STATIC_API_KEY")
        return context


class EventBadgesPdf(EventView):
    def get(self, request, *args, **kwargs):
        event = self.get_object()
        registrations = event.registrations.filter(is_accepted=True).select_related("user__profile")
        maker = BadgesPdfMaker(registrations=registrations, filename="badges.pdf")
        return maker.response


class EventAbstractsSheet(EventView):
    def get(self, request, *args, **kwargs):
        return AbstractsSheet(filename=f"{self.get_object().code}.xlsx", queryset=self.get_object().abstracts).response


class EventRegistrationsSheet(EventView):
    def get(self, request, *args, **kwargs):
        return RegistrationsSheet(
            filename=f"{self.get_object().code}.xlsx", queryset=self.get_object().registrations
        ).response

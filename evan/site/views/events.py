from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic
from os import environ

from evan.models import Event
from evan.site.views.file_makers.excel import RegistrationsOverview


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
                request, "You don't have the necessary permissions to manage this event.",
            )
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_maps_static_api_key"] = environ.get("GOOGLE_MAPS_STATIC_API_KEY")
        return context


class EventBadgesPdf(EventView):
    def get(self, request, *args, **kwargs):
        pass
        """
        event = self.get_object()
        registrations = event.registrations.select_related('user__profile') \
                             .order_by('user__{0}'.format(event.json_badge['order_by']))
        if 'r' in request.GET:
            registrations = registrations.filter(uuid__in=[request.GET['r']])

        return PDFTemplateResponse(
            request=request,
            template='badges/standard.pdf.html',
            filename='{0}-badges.pdf'.format(event.code),
            context={
                'event': event,
                'registrations': registrations,
            },
            cmd_options={
                'margin-right': 0,
                'margin-left': 0,
            },
            show_content_in_browser=True
        )
        """


class EventSpreadsheet(EventView):
    def get(self, request, *args, **kwargs):
        return RegistrationsOverview(
            filename=f"{self.get_object().code}.xlsx", queryset=self.get_object().registrations
        ).response

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event, Abstract


class AbstractRedirectView(generic.DetailView):
    model = Event
    template_name = "app/abstracts/index.html"

    def get_object(self, queryset=None) -> Event:
        return self.get_event()

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "event"):
            self.event = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.event

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        event = self.get_event()

        if "abstracts" not in event.config or not event.config["abstracts"]:
            messages.error(request, "This event does not allow abstract submission.")
            raise PermissionDenied

        if not event.is_open_for_abstract_submission:
            messages.error(request, "Abstract submission is closed.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class AbstractView(generic.DetailView):
    model = Abstract
    template_name = "app/abstracts/index.html"

    def get_object(self, queryset=None) -> Abstract:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Abstract, uuid=self.kwargs.get("uuid"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        abstract = self.get_object()

        if not abstract.editable_by_user(request.user):
            messages.error(request, "You don't have the necessary permissions to view this abstract submission.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.get_object().event
        return context


class AbstractReviewView(generic.TemplateView):
    template_name = "app/abstracts/review/index.html"

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "event"):
            self.event = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.event

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        event = self.get_event()

        if not event.abstract_reviewers.filter(id=request.user.id).exists():
            messages.error(request, "You don't have the necessary permissions to access this page.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.get_event()
        return context

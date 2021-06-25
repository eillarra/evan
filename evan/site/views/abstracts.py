from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import generic

from evan.models import Event, Abstract


class AbstractRedirectView(generic.DetailView):
    model = Event
    template_name = "app/abstracts/index.html"

    def get_object(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()

        try:
            abstract = event.abstracts.get(user=request.user)
            return redirect(abstract.get_absolute_url())
        except Abstract.DoesNotExist:
            pass

        if "abstracts" not in event.main_config or not event.main_config["abstracts"]:
            messages.error(request, "This event does not allow abstract submission.")
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

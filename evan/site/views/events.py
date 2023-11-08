from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from evan.api.serializers.events import EventListSerializer, ManagedEventSerializer
from evan.models import Event

from .inertia import InertiaView


class EventView(InertiaView):
    vue_entry_point = "apps/event/main.ts"

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_event().editable_by_user(request.user):
            messages.error(
                request,
                "You don't have the necessary permissions to manage this event.",
            )
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_props(self, request, *args, **kwargs) -> dict:
        return {
            "event": ManagedEventSerializer(self.get_event(), context={"request": request}).data,
            "events": EventListSerializer(
                Event.objects_for_user(request.user), many=True, context={"request": request}
            ).data,
        }

    def get_page_title(self, request, *args, **kwargs) -> str:
        return f"{self.get_event().name} - Evan"

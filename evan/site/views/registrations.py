from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from evan.api.serializers.events import EventSerializer
from evan.api.serializers.users import UserSerializer
from evan.models import Event

from .inertia import InertiaView


class RegistrationView(InertiaView):
    vue_entry_point = "apps/registration/main.ts"

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Event, code=self.kwargs.get("code"))
        return self.object

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.get_event().is_open_for_registration:
            messages.error(request, "Registrations are not open for this event.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_props(self, request, *args, **kwargs) -> dict:
        return {
            "user": UserSerializer(request.user, context={"request": request}).data,
            "event": EventSerializer(self.get_event(), context={"request": request}).data,
        }

    def get_page_title(self, request, *args, **kwargs) -> str:
        return f"Registration - {self.get_event().name} - Evan"

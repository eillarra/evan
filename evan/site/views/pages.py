from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ViewDoesNotExist
from django.utils.decorators import method_decorator

from evan.api.serializers.contents import ContentSerializer
from evan.api.serializers.events import EventListSerializer
from evan.api.serializers.registrations import AuthRegistrationRetrieveSerializer
from evan.api.serializers.sessions import SessionSerializer
from evan.models import Content, Event, Permission, Session

from .inertia import CachedInertiaView, InertiaView


def get_contents(key_prefix: str):
    """Get contents from the database."""
    return {
        content.key: ContentSerializer(content).data for content in Content.objects.filter(key__startswith=key_prefix)
    }


class HomeView(CachedInertiaView):
    """Home page."""

    vue_entry_point = "apps/home/main.ts"


class DashboardView(InertiaView):
    """Authenticated user's dashboard."""

    vue_entry_point = "apps/dashboard/main.ts"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_props(self, request, *args, **kwargs):
        managed_events = Event.objects.filter(acl__user_id=request.user.id, acl__level__gte=Permission.ADMIN)

        return {
            "managed_events": EventListSerializer(managed_events, many=True, context={"request": request}).data,
            "registrations": AuthRegistrationRetrieveSerializer(
                request.user.registrations, many=True, context={"request": request}
            ).data,
        }


class SessionSecretEditorView(InertiaView):
    """Session edit view that can only be accessed via a complex URL."""

    vue_entry_point = "apps/session/main.ts"

    def get_props(self, request, *args, **kwargs):
        try:
            session = Session.objects.get(uuid=kwargs["uuid"])
        except Session.DoesNotExist as exc:
            raise ViewDoesNotExist from exc

        if session.secret != kwargs["secret"]:
            raise PermissionDenied

        return {
            "event": EventListSerializer(session.event, context={"request": request}).data,
            "secret": kwargs["secret"],
            "session": SessionSerializer(session, context={"request": request}).data,
        }

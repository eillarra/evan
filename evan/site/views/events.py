import polars as pl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from evan.api.serializers.events import EventListSerializer, ManagedEventSerializer
from evan.models import Event
from evan.services.excel import DataSheet, ExcelView

from .inertia import InertiaView


class EventFirewallMixin(View):
    """Mixin to check if the user has permission to manage the event."""

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


class EventView(EventFirewallMixin, InertiaView):
    vue_entry_point = "apps/event/main.ts"

    def get_props(self, request, *args, **kwargs) -> dict:
        return {
            "event": ManagedEventSerializer(self.get_event(), context={"request": request}).data,
            "events": EventListSerializer(
                Event.objects_for_user(request.user), many=True, context={"request": request}
            ).data,
        }

    def get_page_title(self, request, *args, **kwargs) -> str:
        return f"{self.get_event().name} - Evan"


class EventExcelView(EventFirewallMixin, ExcelView):
    """A view that generates an Excel file with event registrations."""

    def get_filename(self) -> str:
        """Get the filename, without extension."""
        return f"{self.get_event().code}_{self.kwargs.get('file_code')}"

    def get_sheets(self) -> list[DataSheet]:
        """Get the sheets of the Excel file.

        :raises NotImplementedError: If the file code is not implemented.
        """
        try:
            return {
                "registrations": get_registration_sheets,
            }[self.kwargs.get("file_code")](self.get_event())
        except KeyError as exc:
            raise NotImplementedError from exc


def get_registration_sheets(event: Event) -> list[DataSheet]:
    """Get the sheets with an overview of the event registrations."""
    rows = []

    for registration in event.registrations.filter(is_accepted=True).select_related("user"):  # type: ignore
        rows.append(
            {
                "uuid": str(registration.uuid),
                "email": registration.user.email,
                "user": registration.user.name,
                "affiliation": registration.user.affiliation,
                "registration_type": registration.fee_type,
                "base_fee": registration.base_fee,
                "extra_fees": registration.extra_fees + registration.manual_extra_fees,
                "total_fee": registration.total_fee,
                "is_paid": registration.is_paid,
                "visa_requested": registration.visa_requested,
                "gender": registration.user.extra_data.get("gender"),
                "dietary": registration.user.extra_data.get("dietary"),
                "special_needs": registration.user.extra_data.get("special_needs"),
            }
        )

    sheets = [(pl.DataFrame(rows), "REGISTRATIONS")]

    for social_event in event.sessions.filter(is_social_event=True):  # type: ignore
        rows = []

        for registration in social_event.registrations.filter(is_accepted=True).select_related("user"):
            rows.append(
                {
                    "uuid": str(registration.uuid),
                    "email": registration.user.email,
                    "user": registration.user.name,
                    "affiliation": registration.user.affiliation,
                    "dietary": registration.user.extra_data.get("dietary"),
                    "special_needs": registration.user.extra_data.get("special_needs"),
                }
            )

            for person in registration.extra_data.get("accompanying_persons", []):
                if social_event.id in person.get("selected_social_events", []):
                    rows.append(
                        {
                            "uuid": f"-- {registration.uuid}",
                            "email": "-",
                            "user": person.get("name", "-"),
                            "affiliation": "(accompanying)",
                            "dietary": person.get("dietary", "-"),
                            "special_needs": "-",
                        }
                    )

        sheets.append((pl.DataFrame(rows), f"SOCIAL - {social_event.title}"))

    return sheets

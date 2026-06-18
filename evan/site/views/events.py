import json

import polars as pl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from evan.api.serializers.events import EventListSerializer, EventSerializer, ManagedEventSerializer
from evan.api.serializers.sessions import SessionReadOnlySerializer
from evan.api.serializers.users import UserSerializer
from evan.models import Event
from evan.services.excel import DataSheet, ExcelView
from evan.site.pdfs.badges import BadgesPdfMaker

from .inertia import InertiaView


class EventFirewallMixin(View):
    """Mixin to check if the user has permission to manage the event."""

    def get_event(self, queryset=None) -> Event:
        if not hasattr(self, "object"):
            self.object = get_object_or_404(
                Event.objects.prefetch_related(
                    "files",
                    "fees",
                    "sponsors__files",
                    "topics",
                    "tracks",
                    "venues__rooms",
                ),
                code=self.kwargs.get("code"),
            )
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


class EventRegistrationPreviewView(EventFirewallMixin, InertiaView):
    """Renders the registration form in read-only preview mode for event managers.

    Serves the same Vue SPA as the attendee registration view but with the
    ``preview`` flag set, so no registration can be created or updated.
    """

    vue_entry_point = "apps/registration/main.ts"

    def get_event(self, queryset=None) -> Event:
        """Return the event with all prefetches required by the registration form."""
        if not hasattr(self, "object"):
            self.object = get_object_or_404(
                Event.objects.prefetch_related(
                    "files",
                    "fees",
                    "sessions",
                    "sessions__topics",
                    "sessions__subsessions",
                    "sponsors",
                    "sponsors__files",
                    "topics",
                    "tracks",
                    "venues__rooms",
                ),
                code=self.kwargs.get("code"),
            )
        return self.object

    def get_props(self, request, *args, **kwargs) -> dict:
        """Return Inertia props for the registration form preview."""
        event = self.get_event()
        sessions = event.sessions.all()  # type: ignore
        return {
            "user": UserSerializer(request.user, context={"request": request}).data,
            "event": EventSerializer(event, context={"request": request}).data,
            "sessions": SessionReadOnlySerializer(sessions, many=True, context={"request": request}).data,
            "preview": True,
        }

    def get_page_title(self, request, *args, **kwargs) -> str:
        return f"Registration Preview - {self.get_event().name} - Evan"


class EventBadgesPdf(EventFirewallMixin, View):
    """A view that generates a PDF with event badges."""

    def get(self, request, *args, **kwargs):
        event = self.get_event()
        registrations = event.registrations.filter(is_accepted=True).select_related("user")  # type: ignore
        if not event.is_virtual:
            online_only_fee_types = event.fees.filter(online_only=True).values_list("type", flat=True)
            registrations = registrations.exclude(fee_type__in=online_only_fee_types)
        maker = BadgesPdfMaker(registrations=registrations, filename="badges.pdf", as_attachment=False)
        return maker.response


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
    extra_field_codes = [
        field.get("code")
        for field in event.registration_configuration.get("form_fields", [])
        if isinstance(field, dict) and field.get("code")
    ]

    for registration in event.registrations.filter(is_accepted=True).select_related("user", "coupon"):  # type: ignore
        registration_extra_values = {
            code: _get_excel_serializable_extra_value(registration.extra_data.get(code)) for code in extra_field_codes
        }
        rows.append(
            {
                "uuid": str(registration.uuid),
                "email": registration.user.email,
                "user": registration.user.name,
                "affiliation": registration.user.affiliation,
                "country": registration.user.country.name if registration.user.country else "-",
                "registration_type": registration.fee_type,
                "base_fee": registration.base_fee,
                "extra_fees": registration.extra_fees + registration.manual_extra_fees,
                "total_fee": registration.total_fee,
                "is_paid": registration.is_paid,
                "paid_via_coupon": registration.paid_via_coupon,
                "visa_requested": registration.visa_requested,
                "gender": registration.user.extra_data.get("gender"),
                "dietary": registration.user.extra_data.get("dietary"),
                "special_needs": registration.user.extra_data.get("special_needs"),
                **registration_extra_values,
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
                    "country": registration.user.country.name if registration.user.country else "-",
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
                            "country": "-",
                            "dietary": person.get("dietary", "-"),
                            "special_needs": "-",
                        }
                    )

        sheets.append((pl.DataFrame(rows), f"SOCIAL - {social_event.title}"))

    return sheets


def _get_excel_serializable_extra_value(value):
    """Convert extra field values into Excel-safe scalar values."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value

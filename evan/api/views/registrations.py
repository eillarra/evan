from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Registration, lock_capacity_rows

from ..permissions import RegistrationPermission
from ..serializers import AuthRegistrationRetrieveSerializer, RegistrationRetrieveSerializer, RegistrationSerializer
from ..viewsets import EventRelatedViewSet


UGENT_ONLY_REGISTRATION_DETAIL = (
    "This event is only open to UGent-verified users. Please sign in with your UGent account "
    "(or link it to your profile) to register."
)


def lock_requested_capacity(event: Event, validated_data: dict) -> None:
    """Lock the capped fee and sessions that a validated registration payload selects.

    :param event: The event the registration belongs to.
    :param validated_data: The serializer's validated data for the create or update.
    """
    session_ids = {session.pk for session in validated_data.get("sessions", [])}
    for person in validated_data.get("extra_data", {}).get("accompanying_persons", []):
        session_ids.update(person.get("selected_social_events", []))

    lock_capacity_rows(event, fee_type=validated_data.get("fee_type"), session_ids=session_ids)


class RegistrationsViewSet(EventRelatedViewSet):
    queryset = Registration.objects.select_related("coupon", "user").prefetch_related("event")
    serializer_class = RegistrationRetrieveSerializer

    def list(self, request, *args, **kwargs):
        self.serializer_class = RegistrationSerializer
        return super().list(request, *args, **kwargs)


class RegistrationCreateViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Registration.objects.select_related("user").prefetch_related("coupon", "event")
    serializer_class = RegistrationRetrieveSerializer

    def perform_create(self, serializer):
        user = self.request.user
        event = Event.objects.get(code=self.kwargs.get("code"))

        if not event.is_listed and not event.editable_by_user(user):
            raise PermissionDenied("Registrations are not open for this event.")

        if event.registration_audience == Event.RegistrationAudience.UGENT_ONLY and not user.is_ugent_verified:
            raise PermissionDenied(UGENT_ONLY_REGISTRATION_DETAIL)

        if not event.is_open_for_registration:
            raise PermissionDenied("Registrations are not open for this event.")

        try:
            # Capped rows stay locked until commit; session caps are checked after the row is inserted.
            with transaction.atomic():
                lock_requested_capacity(event, serializer.validated_data)
                serializer.save(
                    user=user,
                    event=event,
                )
        except IntegrityError as exc:
            raise ValidationError({"event-user": ["Duplicate entry - this user already has a registration."]}) from exc
        except ValueError as exc:
            raise ValidationError({"non_field_errors": [str(exc)]}) from exc


class RegistrationViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "uuid"
    permission_classes = (RegistrationPermission,)
    queryset = Registration.objects.select_related("user").prefetch_related("sessions", "event")
    serializer_class = AuthRegistrationRetrieveSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                lock_requested_capacity(serializer.instance.event, serializer.validated_data)
                serializer.save()
        except ValueError as exc:
            raise ValidationError({"non_field_errors": [str(exc)]}) from exc

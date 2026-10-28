from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Registration

from ..permissions import RegistrationPermission
from ..serializers import AuthRegistrationRetrieveSerializer, RegistrationRetrieveSerializer, RegistrationSerializer
from ..viewsets import EventRelatedViewSet


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
        has_registration = Registration.objects.filter(event=event, user=user).exists()
        denial = event.registration_access_denied_reason(user, has_registration=has_registration)
        if denial is not None:
            raise PermissionDenied(denial.message)

        try:
            serializer.save(user=user, event=event)
        except IntegrityError as exc:
            raise ValidationError({"event-user": ["Duplicate entry - this user already has a registration."]}) from exc
        except ValueError as exc:
            raise ValidationError({"non_field_errors": [str(exc)]}) from exc


class RegistrationViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "uuid"
    permission_classes = (RegistrationPermission,)
    queryset = Registration.objects.select_related("user", "coupon", "event").prefetch_related("sessions")
    serializer_class = AuthRegistrationRetrieveSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer: serializers.BaseSerializer) -> None:
        """Update the owner's registration, fixing the total fee after the window.

        ``Registration.save()`` and its session M2M signal recalculate the fee, so
        the write happens inside a transaction and is rolled back when the amount
        changes. The pre-save fee is recomputed from the current price table, so a
        later price correction does not read as a change made by this request.

        :param serializer: The validated update serializer.
        :raises ValidationError: When the update would change the total fee.
        """
        user = self.request.user
        event = serializer.instance.event
        # RegistrationPermission already limits this endpoint to the owner.
        denial = event.registration_access_denied_reason(user, has_registration=True, for_update=True)
        if denial is not None:
            raise PermissionDenied(denial.message)

        try:
            with transaction.atomic():
                previous_total = None
                if event.is_registration_window_closed:
                    # Lock the row so a concurrent write cannot slip past the check.
                    serializer.instance = Registration.objects.select_for_update().get(pk=serializer.instance.pk)
                    previous_total = serializer.instance.projected_total_fee()

                registration = serializer.save()

                if previous_total is not None:
                    registration.refresh_from_db()
                    if registration.total_fee != previous_total:
                        raise ValidationError(
                            {
                                "non_field_errors": [
                                    "The registration window has closed; changes that affect the total fee "
                                    "are no longer allowed."
                                ]
                            }
                        )
        except ValueError as exc:
            raise ValidationError({"non_field_errors": [str(exc)]}) from exc

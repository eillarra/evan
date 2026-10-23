from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from evan.models import Event, Registration

from ..permissions import RegistrationPermission
from ..serializers import AuthRegistrationRetrieveSerializer, RegistrationRetrieveSerializer, RegistrationSerializer
from ..viewsets import EventRelatedViewSet


UGENT_ONLY_REGISTRATION_DETAIL = (
    "This event is only open to UGent-verified users. Please sign in with your UGent account "
    "(or link it to your profile) to register."
)


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

        if denial == "audience":
            raise PermissionDenied(UGENT_ONLY_REGISTRATION_DETAIL)
        if denial is not None:
            raise PermissionDenied("Registrations are not open for this event.")

        try:
            serializer.save(user=user, event=event)
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
        user = self.request.user
        event = serializer.instance.event
        # RegistrationPermission already limits this endpoint to the owner.
        denial = event.registration_access_denied_reason(user, has_registration=True)

        if denial == "audience":
            raise PermissionDenied(UGENT_ONLY_REGISTRATION_DETAIL)
        if denial is not None:
            raise PermissionDenied("Registrations are not open for this event.")

        try:
            serializer.save()
        except ValueError as exc:
            raise ValidationError({"non_field_errors": [str(exc)]}) from exc

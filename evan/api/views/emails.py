from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from evan.models import EmailLog, EmailPlan
from evan.services.mailer.base import schedule_email
from evan.services.mailer.emailplans import (
    execute_plan,
    get_random_registration,
    logs_for_plan,
    render_for_registration,
    resolve_recipients_count,
)

from ..permissions import EventRelatedObjectPermission, EventRelatedPermission
from ..serializers.emails import EmailListSerializer, EmailPlanListSerializer, EmailPlanSerializer, EmailSerializer
from ..viewsets import EventRelatedViewSet


class EmailsPermission(EventRelatedPermission):
    allow_create_to_manager = False


class EmailPermission(EventRelatedObjectPermission):
    allow_update_to_manager = False
    allow_delete_to_manager = False


class EmailsViewSet(EventRelatedViewSet):
    queryset = EmailLog.objects.defer("body")
    pagination_class = None
    permission_classes = [EmailsPermission]
    serializer_class = EmailListSerializer


class EmailViewSet(RetrieveModelMixin, GenericViewSet):
    permission_classes = [EmailPermission]
    queryset = EmailLog.objects.all()
    serializer_class = EmailSerializer


class EmailPlansPermission(EventRelatedPermission):
    """EmailPlans are manager-only: list, create, retrieve all require event manager."""

    allow_list_to_all = False
    allow_retrieve_to_all = False
    allow_create_to_manager = True
    allow_update_to_manager = True
    allow_delete_to_manager = True


class EmailPlanPermission(EventRelatedObjectPermission):
    """Detail-level permission: managers can retrieve, update, delete, and trigger custom actions."""

    allow_retrieve_to_all = False
    allow_update_to_manager = True
    allow_delete_to_manager = True
    # Custom actions (preview, demo, send_now, recipients_count, logs) are POST/GET
    # and must be permitted to event managers at object level.
    allow_action_to_manager = True

    def has_permission(self, request, view):
        """Allow authenticated users through to object-level checks.

        The detail viewset is not event-scoped via URL kwargs, so the
        event-related permission class cannot resolve the event here. We defer
        to ``has_object_permission`` for the real check.
        """
        return True

    def has_object_permission(self, request, view, obj):
        """Permit managers for any method (retrieve, update, delete, custom actions).

        :returns: True when the requesting user can manage the plan's event.
        """
        if request.method in ["OPTIONS", "HEAD"]:
            return True
        event = self.get_event(obj)
        if request.method == "GET":
            return self.allow_retrieve_to_all or event.editable_by_user(request.user)
        if request.method in ("PUT", "PATCH"):
            return self.allow_update_to_manager and event.editable_by_user(request.user)
        if request.method == "DELETE":
            return self.allow_delete_to_manager and event.editable_by_user(request.user)
        if request.method == "POST":
            return self.allow_action_to_manager and event.editable_by_user(request.user)
        return False


class EmailPlansViewSet(EventRelatedViewSet, UpdateModelMixin, DestroyModelMixin):
    """CRUD + custom actions for EmailPlans, scoped to an event.

    Custom actions:
      - ``preview``: render subject + body against a random matching registration.
      - ``demo``: send a rendered test email to the requesting user's inbox.
      - ``send_now``: resolve recipients, create one EmailLog per recipient, mark sent.
      - ``logs``: return the EmailLog entries tagged with this plan's id.
    """

    queryset = EmailPlan.objects.select_related("event", "created_by")
    permission_classes = [EmailPlansPermission]
    serializer_class = EmailPlanSerializer
    filterset_fields = ["is_draft", "sent_at"]
    ordering_fields = ["send_at", "created_at", "updated_at"]
    ordering = ["-send_at", "-id"]

    def get_serializer_class(self):
        """Return the lighter list serializer for list responses, full serializer otherwise."""
        if self.action == "list":
            return EmailPlanListSerializer
        return EmailPlanSerializer

    def perform_create(self, serializer):
        """Set ``created_by`` to the requesting user on create."""
        serializer.save(
            event=self.get_event(),
            created_by=self.request.user if self.request.user.is_authenticated else None,
        )

    @action(detail=False, methods=["post"], url_path="recipients_count")
    def recipients_count(self, request, *args, **kwargs):
        """Return the number of registrations matching a filter spec on this event.

        Accepts a ``filters`` JSON body and returns ``{"count": N}``. Used by
        the form to fetch a live recipient count before a plan is saved.

        :returns: ``{"count": N}`` where N is the number of matching registrations.
        """
        filters = request.data.get("filters", {})
        return Response({"count": resolve_recipients_count(self.get_event(), filters)})

    @action(detail=True, methods=["post"])
    def preview(self, request, *args, **kwargs):
        """Render the plan against a random matching registration.

        :returns: ``{"subject": str, "body": str}`` or 404 when no registration matches.
        """
        plan = self.get_object()
        registration = get_random_registration(plan)
        if registration is None:
            return Response({"detail": "No registrations match this filter."}, status=status.HTTP_404_NOT_FOUND)
        subject, body = render_for_registration(plan, registration)
        return Response({"subject": subject, "body": body})

    @action(detail=True, methods=["post"])
    def demo(self, request, *args, **kwargs):
        """Send a rendered demo email to the requesting user's inbox.

        Renders against a random matching registration; returns 404 if none match.
        """
        plan = self.get_object()
        registration = get_random_registration(plan)
        if registration is None:
            return Response({"detail": "No registrations match this filter."}, status=status.HTTP_404_NOT_FOUND)
        subject, body = render_for_registration(plan, registration)
        schedule_email(
            from_email=plan.from_email,
            to=[request.user.email],
            subject=subject,
            text_content=body,
            bcc=plan.bcc,
            reply_to=plan.reply_to,
            log_user=request.user,
            log_event=plan.event,
            tags=[f"emailplan.id:{plan.pk}", "type:emailplan-demo"],
        )
        return Response({"sent": True, "to": request.user.email})

    @action(detail=True, methods=["post"])
    def send_now(self, request, *args, **kwargs):
        """Resolve recipients, create one EmailLog per recipient, mark the plan sent.

        :returns: ``{"sent": count}`` where count is the number of logs created.
        """
        plan = self.get_object()
        count = execute_plan(plan)
        return Response({"sent": count})

    @action(detail=True)
    def logs(self, request, *args, **kwargs):
        """Return the EmailLog entries sent by this plan (tag filtered).

        Uses ``tags__contains`` on MySQL and ``tags__icontains`` on SQLite.
        """
        plan = self.get_object()
        logs = logs_for_plan(plan).defer("body").order_by("-created_at")
        serializer = EmailListSerializer(logs, many=True, context={"request": request})
        return Response(serializer.data)


class EmailPlanViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    """Detail viewset for a single EmailPlan (retrieve / update / delete).

    Custom actions mirror :class:`EmailPlansViewSet` so that ``plan.self +
    'action/'`` URLs resolve without changing the serializer's ``self`` link:
      - ``preview``: render subject + body against a random matching registration.
      - ``demo``: send a rendered test email to the requesting user's inbox.
      - ``send_now``: resolve recipients, create one EmailLog per recipient, mark sent.
      - ``logs``: return the EmailLog entries tagged with this plan's id.
      - ``recipients_count``: return the number of registrations matching a filter spec.
    """

    queryset = EmailPlan.objects.select_related("event", "created_by")
    serializer_class = EmailPlanSerializer
    permission_classes = [EmailPlanPermission]

    @action(detail=True, methods=["post"])
    def preview(self, request, *args, **kwargs):
        """Render the plan against a random matching registration.

        :returns: ``{"subject": str, "body": str}`` or 404 when no registration matches.
        """
        plan = self.get_object()
        registration = get_random_registration(plan)
        if registration is None:
            return Response({"detail": "No registrations match this filter."}, status=status.HTTP_404_NOT_FOUND)
        subject, body = render_for_registration(plan, registration)
        return Response({"subject": subject, "body": body})

    @action(detail=True, methods=["post"])
    def demo(self, request, *args, **kwargs):
        """Send a rendered demo email to the requesting user's inbox.

        Renders against a random matching registration; returns 404 if none match.
        """
        plan = self.get_object()
        registration = get_random_registration(plan)
        if registration is None:
            return Response({"detail": "No registrations match this filter."}, status=status.HTTP_404_NOT_FOUND)
        subject, body = render_for_registration(plan, registration)
        schedule_email(
            from_email=plan.from_email,
            to=[request.user.email],
            subject=subject,
            text_content=body,
            bcc=plan.bcc,
            reply_to=plan.reply_to,
            log_user=request.user,
            log_event=plan.event,
            tags=[f"emailplan.id:{plan.pk}", "type:emailplan-demo"],
        )
        return Response({"sent": True, "to": request.user.email})

    @action(detail=True, methods=["post"])
    def send_now(self, request, *args, **kwargs):
        """Resolve recipients, create one EmailLog per recipient, mark the plan sent.

        :returns: ``{"sent": count}`` where count is the number of logs created.
        """
        plan = self.get_object()
        count = execute_plan(plan)
        return Response({"sent": count})

    @action(detail=True, methods=["post"])
    def recipients_count(self, request, *args, **kwargs):
        """Return the number of registrations matching a filter spec.

        Accepts a ``filters`` JSON body and returns ``{"count": N}``. The plan
        does not need to be saved — the filters in the request body take
        precedence over the plan's stored filters, which lets the form fetch a
        live count before saving.

        :returns: ``{"count": N}`` where N is the number of matching registrations.
        """
        plan = self.get_object()
        filters = request.data.get("filters", plan.filters)
        return Response({"count": resolve_recipients_count(plan.event, filters)})

    @action(detail=True)
    def logs(self, request, *args, **kwargs):
        """Return the EmailLog entries sent by this plan (tag filtered).

        Uses ``tags__contains`` on MySQL and ``tags__icontains`` on SQLite.
        """
        plan = self.get_object()
        logs = logs_for_plan(plan).defer("body").order_by("-created_at")
        serializer = EmailListSerializer(logs, many=True, context={"request": request})
        return Response(serializer.data)

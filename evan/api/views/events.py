from http import HTTPStatus

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from evan.models import Abstract, Event, File, User

from ..permissions import EventAttendeePermission, EventPermission
from ..serializers import AttendeeSerializer, EventSerializer, PublicAbstractSerializer


class EventViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    lookup_field = "code"
    permission_classes = (EventPermission,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @method_decorator(never_cache)
    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.prefetch_related(
            "fees",
            "papers__topics",
            "papers__files",
            "sessions__topics",
            "sponsors__files",
            "topics",
            "tracks",
            "venues__rooms",
        )
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["get"],
        pagination_class=None,
        permission_classes=(EventAttendeePermission,),
        serializer_class=AttendeeSerializer,
    )
    @method_decorator(never_cache)
    def attendees(self, request, *args, **kwargs):
        self.queryset = User.objects.filter(registrations__event_id=self.get_object().id)
        return ListModelMixin.list(self, request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=(EventAttendeePermission,),
    )
    @method_decorator(never_cache)
    def contact(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied

        import evan.tasks.emails

        event = self.get_object()
        user = User.objects.get(id=self.request.data["user_id"])
        sender = self.request.user

        # Check if target user can be contacted
        # Event managers can contact any registered user (bypassing contact preferences)
        # Regular attendees can only contact other registered users who allow contact
        if event.editable_by_user(sender):
            # Event managers can contact any user registered for their event
            if not event.registrations.filter(user_id=user.id).exists():
                raise PermissionDenied("User cannot be contacted.")
        else:
            # Regular attendees must respect contact preferences and registration status
            if not user.can_be_contacted() or not event.registrations.filter(user_id=user.id).exists():
                raise PermissionDenied("User cannot be contacted.")

        try:
            email = (
                "_emails/contact.md.html",
                f"You have received a message for #{event.hashtag} (via Evan)",
                "Ghent University <no-reply@ugent.be>",
                [user.email],
                {
                    "event_name": event.name,
                    "event_hashtag": event.hashtag,
                    "user_first_name": user.first_name,
                    "sender_email": sender.email,
                    "sender_first_name": sender.first_name,
                    "sender_name": f"{sender.first_name} {sender.last_name}",
                    "sender_affiliation": sender.affiliation,
                    "message": self.request.data["message"],
                },
            )
            evan.tasks.emails.send_template_email(*email)

            return Response({"detail": "Your message has been sent."})

        except Exception:
            return Response({"detail": "We could not send your message."}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    @action(
        detail=True,
        methods=["post"],
        pagination_class=None,
        serializer_class=EventSerializer,
        parser_classes=[FileUploadParser],
    )
    @method_decorator(never_cache)
    def files(self, request, *args, **kwargs):
        file_tags = request.query_params.get("tags", None)
        file_type = request.query_params.get("type", File.PRIVATE)
        file_type = file_type if file_type in [File.PUBLIC, File.PRIVATE] else File.PRIVATE
        file = File(content_object=self.get_object(), type=file_type, tags=file_tags, file=request.data["file"])
        file.save()
        return self.retrieve(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["get"],
        pagination_class=None,
        serializer_class=PublicAbstractSerializer,
    )
    @method_decorator(never_cache)
    def public_abstracts(self, request, *args, **kwargs):
        self.queryset = Abstract.objects.filter(event_id=self.get_object().id, is_accepted=True).prefetch_related(
            "files"
        )
        return ListModelMixin.list(self, request, *args, **kwargs)

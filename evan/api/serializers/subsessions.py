from django.core.exceptions import ValidationError
from rest_framework import serializers

from evan.models import Session, Subsession, validate_datetime

from .rel.files import FilesMixin


class SubsessionReadOnlySerializer(serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:subsession-detail")

    class Meta:
        model = Subsession
        exclude = ["session", "created_at", "uuid", "program"]


class SubsessionSerializer(FilesMixin, serializers.ModelSerializer):
    self = serializers.HyperlinkedIdentityField(view_name="v1:subsession-detail")

    class Meta:
        model = Subsession
        exclude = ["session", "created_at", "uuid"]
        read_only_fields = ["id", "session", "updated_at"]

    def validate(self, data):
        if not self.instance:
            session_id = self.context["view"].kwargs.get("parent_lookup_session_id")
            session = Session.objects.get(id=session_id)
        else:
            session = self.instance.session

        if "start_at" in data and data["start_at"]:
            validate_datetime(data["start_at"], session.event)

            if session.start_at and data["start_at"] < session.start_at:
                raise serializers.ValidationError(
                    {"start_at": "Subsession start time cannot be before session start time."}
                )

        if "end_at" in data and data["end_at"]:
            validate_datetime(data["end_at"], session.event)

            if session.end_at and data["end_at"] > session.end_at:
                raise serializers.ValidationError({"end_at": "Subsession end time cannot be after session end time."})

        start_at = data.get("start_at") or (self.instance.start_at if self.instance else None)
        end_at = data.get("end_at") or (self.instance.end_at if self.instance else None)

        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError({"start_at": "Subsession start time must be before end time."})

        return data

    def save(self, **kwargs):
        """Override save to convert Django ValidationError to DRF ValidationError."""
        try:
            return super().save(**kwargs)
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError for proper 400 status
            if hasattr(e, "message_dict"):
                # ValidationError with field-specific errors
                raise serializers.ValidationError(e.message_dict) from e
            else:
                # ValidationError with general errors
                raise serializers.ValidationError(e.messages if hasattr(e, "messages") else str(e)) from e


class SubsessionWithSecretsSerializer(SubsessionSerializer):
    program_validation = serializers.SerializerMethodField()
    program_paper_references = serializers.SerializerMethodField()

    class Meta:
        model = Subsession
        exclude = ["session"]
        read_only_fields = [
            "id",
            "session",
            "created_at",
            "updated_at",
            "uuid",
            "secret",
            "program_validation",
            "program_paper_references",
        ]

    def get_program_validation(self, obj):
        return obj.validate_program_template()

    def get_program_paper_references(self, obj):
        return obj.get_program_paper_references()

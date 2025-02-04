import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .files import FileUploaderConfig


class ContentConfig(BaseModel):
    """Content model configuration."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    markdown: bool = Field(default=False, description="Whether the content is written in markdown.")
    file_uploader: FileUploaderConfig = Field(default=None, description="File uploader configuration.")


def get_validated_content_configuration(config):
    """Validate a content configuration.

    :returns: The validated dictionary with default values if not provided.
    :raises ValueError: If the configuration is invalid."""
    try:
        return json.loads(ContentConfig(**config).model_dump_json())
    except (TypeError, ValidationError) as exc:
        raise ValueError(exc) from exc

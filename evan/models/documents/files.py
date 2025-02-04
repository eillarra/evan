from typing import Literal

from pydantic import BaseModel, ConfigDict, conint


class BaseFileUploaderConfig(BaseModel):
    """File uploader configuration."""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    label: str = "Upload file"
    max_files: conint(gt=0, lt=100) = 1  # type: ignore
    accept: str = "*"
    allowed_visibility: list[Literal["public", "private"]] = ["public", "private"]
    default_visibility: Literal["public", "private"] = "private"


FileUploaderConfig = BaseFileUploaderConfig | None

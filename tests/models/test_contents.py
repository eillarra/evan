import pytest
from django.core.exceptions import ValidationError

from tests._factories import ContentFactory


@pytest.fixture
def content(db, t_event):
    return ContentFactory(event=t_event)


@pytest.mark.django_db
def test_valid_configuration(content):
    content.config = {"file_uploader": {"max_files": 1}}
    content.clean()
    assert content.configuration["file_uploader"]["max_files"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_config",
    [
        {"file_uploader": {"max_files": 0}},
    ],
)
def test_invalid_configuration(content, invalid_config):
    content.config = invalid_config
    with pytest.raises(ValidationError):
        content.save()

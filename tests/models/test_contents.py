import pytest
from django.core.exceptions import ValidationError

from evan.utils.factories import ContentFactory


@pytest.fixture
def content(db, test_event):
    return ContentFactory(event=test_event)


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
        {"wrong_key": {"max_files": 1}},
        {"file_uploader": {"wrong_key": 1}},
    ],
)
def test_invalid_configuration(content, invalid_config):
    content.config = invalid_config
    with pytest.raises(ValidationError):
        content.save()

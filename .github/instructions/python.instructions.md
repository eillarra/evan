---
applyTo: '**/*.py'
description: Python, Django, and Pytest coding standards for the project.
---

## General

- All code must be PEP 8 compliant.
- All function signatures must use type hints.

## Docstring format (reStructuredText)

- All public functions, methods, and modules **must** have a docstring.
- The format must be reStructuredText (reST) to be compatible with Sphinx.
- Provide clear descriptions for parameters, return values, and any exceptions raised.
- Do not include type information, as it is already in the function signature.
- All `:param`, `:returns`, and `:raises` descriptions must end with a period (`.`) for consistency.

  > ```python
  > def get_user_by_id(user_id: int, is_active: bool = True) -> User | None:
  >     """Fetch a user from the database by their primary key.
  >
  >     :param user_id: The primary key of the user to retrieve.
  >     :param is_active: If True, only search for active users.
  >     :returns: The User object or None if not found.
  >     :raises User.DoesNotExist: If no user with the given ID is found.
  >     """
  >     # ... function implementation ...
  >     pass
  > ```

## Django

- Follow the "Fat Models, Thin Views" principle. Business logic belongs in models or managers.
- Prefer Class-Based Views (CBVs) over function-based views.
- Use the ORM efficiently. Prevent N+1 problems with `select_related` and `prefetch_related`.

## Command execution (CRITICAL)

- Rule: all Django and Python commands **must be prefixed with `./run`**.
- This is a required executable script in the project root that sets up the environment and runs commands within it.

- Correct examples:
  > ```bash
  > ./run python manage.py migrate
  > ./run pytest -k sessions
  > ```

## Testing (pytest)

We test **behavior**, not functions. We test **boundaries**, not external libraries.

### General rules

- All new code requires tests.
- Structure tests using the Arrange-Act-Assert (AAA) pattern.
- Use `@pytest.fixture` for setup and `@pytest.mark.parametrize` for testing multiple inputs.

### File naming conventions

Test files should be named to clearly indicate what aspect they test. Use these suffixes:

| Suffix            | Purpose                                               | Example                            |
| ----------------- | ----------------------------------------------------- | ---------------------------------- |
| `_permissions.py` | Permission/access control tests by user role          | `test_jobs_permissions.py`         |
| `_api.py`         | API behavior tests (CRUD operations, response format) | `test_jobs_api.py`                 |
| `_serializers.py` | Serializer field validation, read/write behavior      | `test_registration_serializers.py` |
| `_validation.py`  | Input validation and business rule tests              | `test_coupon_validation.py`        |
| (no suffix)       | Model tests, service tests, or mixed tests            | `test_jobs.py`, `test_payments.py` |

### Permission tests pattern (inheritance-based)

For API endpoints, use the inheritance pattern to test permission levels. This ensures consistent coverage across user roles:

```python
@pytest.mark.api
class TestForAnonymous:
    """Tests for anonymous users."""

    expected_status_codes: dict[str, status] = {
        "list": status.OK,
        "create": status.FORBIDDEN,
        "retrieve": status.OK,
        "update": status.FORBIDDEN,
        "delete": status.FORBIDDEN,
    }

    def test_list(self, api_client, resource):
        response = api_client.get(url)
        assert response.status_code == self.expected_status_codes["list"]


class TestForAuthenticated(TestForAnonymous):
    """Tests for authenticated users (no special permissions)."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, t_user):
        api_client.force_authenticate(user=t_user)


class TestForOwner(TestForAuthenticated):
    """Tests for resource owners."""

    expected_status_codes = {
        "list": status.OK,
        "create": status.CREATED,
        "retrieve": status.OK,
        "update": status.OK,
        "delete": status.NO_CONTENT,
    }
```

### Test class naming

- **Permission tests**: `TestForAnonymous`, `TestForAuthenticated`, `TestForOwner`, `TestForManager`, `TestForStaff`
- **Behavior tests**: `TestJobCreate`, `TestJobUpdate`, `TestCouponValidation`
- **Serializer tests**: `TestJobSerializer`, `TestRegistrationSerializer`

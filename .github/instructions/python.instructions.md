---
applyTo: "**/*.py"
description: Python, Django, and Pytest coding standards for the project.
---

General
-------

- All code must be PEP 8 compliant.
- All function signatures must use type hints.

Docstring format (reStructuredText)
-----------------------------------

- All public functions, methods, and modules **must** have a docstring.
- The format must be reStructuredText (reST) to be compatible with Sphinx.
- Provide clear descriptions for parameters, return values, and any exceptions raised.
- Do not include type information, as it is already in the function signature.

  > ```python
  > def get_user_by_id(user_id: int, is_active: bool = True) -> User | None:
  >     """Fetch a user from the database by their primary key.
  >
  >     :param user_id: The primary key of the user to retrieve.
  >     :param is_active: If True, only search for active users.
  >     :raises User.DoesNotExist: If no user with the given ID is found.
  >     :returns: The User object or None if not found.
  >     """
  >     # ... function implementation ...
  >     pass
  > ```

Django
------

- Follow the "Fat Models, Thin Views" principle. Business logic belongs in models or managers.
- Prefer Class-Based Views (CBVs) over function-based views.
- Use the ORM efficiently. Prevent N+1 problems with `select_related` and `prefetch_related`.

Testing (pytest)
----------------

- All new code requires tests.
- Structure tests using the Arrange-Act-Assert (AAA) pattern.
- Use `@pytest.fixture` for setup and `@pytest.mark.parametrize` for testing multiple inputs.

Command execution (CRITICAL)
----------------------------

- Rule: all Django and Python commands **must be prefixed with `./run.sh`**.
- This is a required executable script in the project root that sets up the environment and runs commands within it.

- Correct examples:
  > ```bash
  > ./run.sh python manage.py migrate
  > ./run.sh pytest -k sessions
  > ```

# Agent guidance for Evan

This file is the canonical source of truth for AI coding agents working in this repo.
Aliases: `CLAUDE.md` and `.github/copilot-instructions.md` are symlinks to this file.

## Core philosophy

- **Proactive collaboration**: do not blindly follow instructions. If a request is ambiguous, overly complex, or risky, challenge it and suggest a better alternative.
- **Maintainability first**: prioritise code that is easy to read, understand, and modify.
- **Simplicity (KISS & YAGNI)**: favour the most straightforward solution. Do not add functionality that has not been explicitly requested.
- **Consistency over novelty**: follow existing codebase conventions. Only introduce new patterns when clearly justified.

## Code generation style

- **Self-documenting code**: clear, unabbreviated names. Decompose into single-purpose functions. Use type hints.
- **Strategic commenting**: avoid comments explaining _what_ code does. Only comment _why_ when not obvious.
- **Testability**: write code that is easy to test. Prefer pure functions and clear interfaces.

## Stack

- **Backend**: Django 6 + DRF (drf-extensions for nested routers), Python 3.14, managed with uv.
- **Frontend**: Vue 3 + Quasar + Pinia + Inertia.js + Vite + TypeScript, managed with yarn 4 (Berry) — lives in `vue/`.
- **Background jobs**: huey (`evan/tasks/`), Redis-backed in production.
- **DB**: MySQL in production, SQLite (`dev.db`) in dev/test.
- **Storage**: S3 via django-storages + boto3 (UGent S3 endpoint).
- **Auth**: django-allauth (GitHub, Google, LinkedIn, UGent provider).
- **Admin**: django-unfold.
- **i18n**: en + nl (Dutch is the default `LANGUAGE_CODE`).
- **Observability**: Sentry SDK (Django + Redis integrations) backend; `@sentry/vue` frontend.

## Commands

A `./run` wrapper exists — **all backend commands must be prefixed with `./run`**. It loads `.env` and invokes `uv run --env-file .env`. Do not call `uv` / `pytest` / `python manage.py` directly. Frontend commands use `yarn` directly (not through `./run`).

## Commit conventions

Conventional Commits. Short form: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`, `perf: ...`.
Optional scope: `type(scope): description` (e.g. `fix(api): handle missing event code`).
Imperative mood, lowercase, no trailing period.
Breaking change: `feat!: ...` or a `BREAKING CHANGE:` footer.
Never use vague messages like `wip` or `update`.

## Git workflow

- Always branch from `main`. Never branch from another feature branch.
- Branch naming: `type/short-description` in kebab-case (`feat/results-import`, `fix/ranking-tiebreak`).
- Open a PR as soon as the branch has meaningful work — draft PRs are fine.
- The PR title becomes the squash-merge commit, so write it as a conventional commit.
- One PR per logical change — do not bundle unrelated fixes.

## Testing

Testing conventions are language-specific. See Python → "Testing (pytest)" below and TypeScript → "Testing (vitest)". Django-specific test patterns (markers, file-suffix conventions, permission-inheritance) live in the Django section.

---

# Python

## General

- All code must be PEP 8 compliant.
- All function signatures must use type hints.

## Docstring format (reStructuredText)

- All public functions, methods, and modules **must** have a docstring.
- Format is reStructuredText (reST) to be compatible with Sphinx.
- Provide clear descriptions for parameters, return values, and any exceptions raised.
- Do not include type information — it is already in the function signature.
- All `:param`, `:returns`, and `:raises` descriptions must end with a period (`.`).

```python
def get_user_by_id(user_id: int, is_active: bool = True) -> User | None:
    """Fetch a user from the database by their primary key.

    :param user_id: The primary key of the user to retrieve.
    :param is_active: If True, only search for active users.
    :returns: The User object or None if not found.
    :raises User.DoesNotExist: If no user with the given ID is not found.
    """
    # ... function implementation ...
```

## Commands (Python)

```
./run pytest --cov=evan --cov-report=term      # full test suite with coverage
./run ruff format .                             # format
./run ruff check evan                           # lint (must be clean before commit)
```

## Testing (pytest)

We test **behaviour**, not functions. We test **boundaries**, not external libraries.

- All new code requires tests.
- Tests live in `tests/`, never inline next to source (no `tests.py` inside package modules).
- Structure tests using the Arrange-Act-Assert (AAA) pattern.
- Use `@pytest.fixture` for setup and `@pytest.mark.parametrize` for testing multiple inputs.
- Fixtures and factories: `tests/_factories/` (factory-boy), `tests/conftest.py`. Reuse them; do not redefine model factories per test.
- Anything touching the filesystem or external services must be guarded/mocked. Never hit the production DB or live APIs in tests.
- Coverage config lives in `pyproject.toml` (`[tool.coverage.*]`); data in `.coverage_py/`.

### Test-review workflow

When asked to review, audit, or add tests to existing code, apply this sequence:

1. **Read the tests first.** Critically evaluate each test: does the assertion actually verify the claimed behaviour, or is it trivially true? Are edge cases and failure paths covered? Are there implicit assumptions that could make the test fragile?
2. **Adjust the tests** to fix any identified weaknesses before running them.
3. **Run the adjusted suite.** A failing test after adjustment is valuable — it reveals a real bug in production code.
4. **Fix the production code** to make failing tests pass — never weaken a test to force it green.

## Ruff

- Ruff handles both linting and formatting. Config lives in `pyproject.toml`.
- Rule sets: `E`, `F`, `UP`, `B`, `SIM`, `I`, `DJ`; `SIM105` is ignored. `target-version = "py314"`, `line-length = 120`.
- isort: `lines-after-imports = 2`.
- Do not inline-ignore without a justification comment.
- Run `./run ruff format . && ./run ruff check evan` before committing. CI enforces a clean tree.

---

# Django

## General

- Follow the "Fat Models, Thin Views" principle. Business logic belongs in models or managers; views stay thin. Complex cross-model operations go in `evan/services/`.
- Prefer Class-Based Views / ViewSets over function-based views.
- Use the ORM efficiently. Prevent N+1 with `select_related` (FK / one-to-one) and `prefetch_related` (M2M / reverse). Prefer `values()` / `values_list()` when you only need a few columns.
- Avoid raw SQL unless the ORM genuinely cannot express the query efficiently.

## Migrations

- Never edit a shipped migration. Always `./run python manage.py makemigrations evan` to create a new one.
- Data migrations go in their own migration file; keep them reversible where possible.
- Run `./run python manage.py makemigrations --check evan` locally to catch drift before CI.

## API (DRF)

- All public endpoints live under `/api/v1/`. Versioning is by URL prefix (NamespaceVersioning), not header.
- Router is `NestedRouterMixin` + `DefaultRouter` (drf-extensions), defined in `evan/api/routers.py`. Every viewset must be registered there with an explicit `basename`.
- Serializers in `evan/api/serializers/`, permissions in `evan/api/permissions/`, views in `evan/api/views/`.
- Auth: `SessionAuthentication` + `TokenAuthentication`.
- Renderer: JSON only (`JSONRenderer`). Pagination: `PageNumberPagination`, page size 50.
- Response format: JSON, ISO 8601 UTC dates, ISO 3166-1 alpha-2 country codes. Errors use `{"detail": "..."}` (DRF default).
- `COERCE_DECIMAL_TO_STRING = False` — decimals are returned as numbers, not strings.

## Commands (Django-specific)

```
./run server                                       # Django dev server
./run huey                                         # huey worker
./run python manage.py makemigrations evan         # new migration
./run python manage.py migrate                     # apply migrations
./run python manage.py makemigrations --check evan # CI drift check
```

## Testing (Django-specific patterns)

- Backend settings module: `DJANGO_SETTINGS_MODULE = "evan.settings.test"` (set in `pyproject.toml`).
- Markers: `@pytest.mark.api` (API tests), `@pytest.mark.site` (site/Django-view tests).
- Key fixtures in `tests/conftest.py`: `api_client` (DRF `APIClient` with CSRF enforcement), `t_event`, `t_event_manager`, `t_superuser`.

### Test file naming suffixes

Test files are named to indicate what aspect they test:

| Suffix | Purpose | Example |
| --- | --- | --- |
| `_permissions.py` | Permission / access-control tests by user role | `test_registrations_permissions.py` |
| `_api.py` | API behaviour tests (CRUD, response format) | `test_users_api.py` |
| (no suffix) | Model tests, service tests, or mixed tests | `test_events.py`, `test_venues.py` |

### Permission tests (inheritance pattern)

For HTTP API endpoints, use an inheritance pattern to cover permission levels consistently:

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

- **Permission tests**: `TestForAnonymous`, `TestForAuthenticated`, `TestForOwner`, `TestForManager`, `TestForStaff`.
- **Behaviour tests**: `TestJobCreate`, `TestJobUpdate`, `TestCouponValidation`.
- **Serializer/schema tests**: `TestJobSerializer`, `TestRegistrationSerializer`.

---

# TypeScript

## General

- TypeScript is mandatory; no plain JS source.
- All function signatures use explicit types; no `any` without a justification comment explaining why a narrower type is impossible. Prefer `unknown` over `any` when accepting untrusted input; narrow it with type guards.
- `strict` is enabled in `tsconfig.json` (plus `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`). Do not relax compiler flags to silence a single error — fix the code.
- Path alias: `@` → `vue/src` (configured in `tsconfig.json` and `vite.config.ts`).

## Style

- Prettier + ESLint: config in `.eslintrc.js` / `.prettierrc`.
- **Package manager:** yarn 4 (Berry; `corepack enable` then `yarn`). Run all frontend commands via `yarn` directly — the frontend is not run through `./run`.
- Editor defaults: see `.editorconfig`.

## Testing (vitest)

We test **behaviour**, not functions. We test **boundaries**, not external libraries.

- All new code requires tests.
- Tests colocate as `*.test.ts` in `__tests__/` dirs next to the module under test (e.g. `vue/src/apps/registration/components/__tests__/FeeFormComponent.test.ts`). Never inline next to source.
- Structure tests using Arrange-Act-Assert.
- Mock external APIs / HTTP calls — never hit the backend or live services from unit tests.
- Coverage via `@vitest/coverage-v8`; reports to `.coverage_ts/`. Config in `vite.config.ts`.

### The "black box" rule

Test the public API of your modules. Do not test private methods or internal implementation details. If you refactor internal code but the output stays the same, tests should not break.

### The "not our code" rule

Assume external libraries work as advertised. Do not write tests to verify library behaviour.

- ❌ Testing the library: asserting that `date-fns(date).format()` returns a string tests `date-fns`, not us.
- ❌ Testing the mock: mocking a function and asserting it returns what you told it to return.
- ✅ Testing integration: asserting that _our_ code handles the library's success/failure correctly.

### Functionality over implementation

Test _what_ the result is, not _how_ we got it. Do not spy on internal method calls.

```typescript
// ❌ BAD: Brittle, tied to implementation
it('should call validateInput then calculateTax', () => {
  const spy1 = vi.spyOn(service, 'validateInput');
  service.processOrder(100);
  expect(spy1).toHaveBeenCalled();
});

// ✅ GOOD: Robust, tests behaviour
it('should return the total price including 20% tax', () => {
  const result = service.processOrder(100);
  expect(result.total).toBe(120);
});
```

### Boundary testing

When using external libraries, mock the **boundary**, not the logic. Test _our reaction_ to external success/failure.

```typescript
// ❌ BAD: Testing if our mock works
it('axios should return data', async () => {
  mockAxios.get.mockResolvedValue({ data: 'foo' });
  const result = await axios.get('/url');
  expect(result.data).toBe('foo');
});

// ✅ GOOD: Testing our error handling
it('should throw CustomLibError when the network fails', async () => {
  mockAxios.get.mockRejectedValue(new Error('Network Error'));
  await expect(myLibrary.fetchData()).rejects.toThrow(CustomLibError);
});
```

## Things to avoid (TypeScript-specific)

- Do not commit `dist/`, `node_modules/`, build artifacts (see `.gitignore`).

---

# Vue

## Stack

- **Vue 3** with the Composition API — `<script setup lang="ts">` is mandatory. No Options API.
- **State management:** Pinia is the only state management library.
- **Component library:** Quasar. Prefer Quasar components (`<q-btn>`) over native HTML; use Quasar utility classes (`q-pa-md`, `row`) instead of custom CSS.
- **Build / dev server:** Vite. One entry per Inertia app in `vue/src/apps/` (dashboard, event, home, registration, registrationAfter, session).
- **Server-rendered glue:** Inertia.js — Django renders the right page component and provides props; the Vue frontend follows TypeScript + Vue rules independently.
- **Sentry:** `@sentry/vue` when configured. See the Sentry section below.
- **i18n:** vue-i18n (`vue/src/locales/`).
- Package manager: yarn 4 (Berry; `corepack enable` then `yarn`).

## Reactivity best practices

### Choosing the right ref type

| Type | Use for | Example |
| :--- | :--- | :--- |
| `ref` | Primitives, small objects where deep reactivity is needed | `ref(0)`, `ref({ name: '' })` |
| `shallowRef` | Large arrays, objects from API responses | `shallowRef<User[]>([])` |
| `readonly` | Exposing state that should not be mutated | `readonly(state)` in composables |

### Guidelines

- **API responses:** always use `shallowRef` for data fetched from APIs to avoid the performance cost of deep reactivity.
- **Updating `shallowRef`:** always replace the `.value` entirely — do not mutate nested fields.
- Expose read-only state from composables via `readonly()`; keep the writable ref internal.

## Component structure

- **File order:** `<style scoped>` → `<template>` → `<script setup lang="ts">` (follow the order already used in existing components — do not mix).
- **Naming:** `PascalCase.vue` for components, `useSomething.ts` for composables.
- **Quasar:** prefer Quasar components (`<q-btn>`, `<q-input>`, …) over native HTML. Use Quasar utility classes (`q-pa-md`, `row`, `col`) instead of custom CSS wherever possible.
- **`<script setup lang="ts">`** is mandatory — no Options API, no `defineComponent({})` unless a specific feature requires it.

## Code organisation for testability

- **Pure functions** (`vue/src/utils/`): stateless, no Vue imports. Testable in isolation.
- **Composables** (`vue/src/composables/`): stateful, use Vue reactivity. Tested by calling the composable and asserting on returned refs.
- Do not write complex transformation logic inside `<script setup>`. Extract it to a pure function (utils) or a composable so it can be tested in isolation.

## Form components

- Form components library: `vue/src/components/forms/`. Reusable form inputs and dialogs (ColorInput, DateSelect, DialogForm, MarkedTextarea, ProgramTemplateEditor, ReadonlyField, SelectorDialog).

## Commands (Vue-specific)

```
corepack enable        # one-time, enables yarn 4
yarn                   # install deps
yarn dev               # vite dev server (Inertia hot reload)
yarn build             # production build
yarn lint              # eslint
yarn format            # prettier --write
yarn test:unit         # vitest
```

## Testing (Vue-specific)

- Use `@vue/test-utils` for component mounting; `happy-dom` for the DOM environment.
- Mock axios / Inertia router / Quasar plugins as needed — never hit the backend from unit tests.
- **Composables** usually do not need to be mounted in a component — call the composable directly and assert on the returned refs.

```typescript
describe('usePagination', () => {
  it('navigates to the next page', () => {
    const { page, nextPage } = usePagination({ total: 100 });
    nextPage();
    expect(page.value).toBe(2);
  });
});
```

## Things to avoid (Vue-specific)

- Do not put API-calling business logic in components — push it into a Pinia store or composable.
- Do not import backend Python types into the frontend; maintain TS types in `vue/src/types/`.

---

## Error monitoring (Sentry)

You have access to the Sentry MCP server. Use it to investigate errors proactively when debugging issues.

- **`regionUrl`**: https://de.sentry.io
- **`organizationSlug`**: ea06
- **`projectSlugOrId`**: evan-backend    ← backend (Django) service
- **`projectSlugOrId`**: evan-frontend ← Vue/TS app

When resolving issues, prefer **`resolvedInNextRelease`** over `resolved` — this signals the fix is in the next deployment rather than already live.

### Bug fix workflow

When a Sentry issue reveals a bug that is not covered by an existing test, always add a regression test before (or alongside) the fix:

1. **Reproduce first**: write a test that fails against the current code, confirming you have isolated the root cause.
2. **Fix the code**: make the test pass.
3. **Verify no new gaps**: confirm no related paths are left uncovered.

Never close a Sentry bug without a corresponding regression test. The fix lives in the code; the test ensures it stays fixed.

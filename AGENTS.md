# Agent guidance for Evan

Canonical agent instructions; `CLAUDE.md` and `.github/copilot-instructions.md` symlink here.

## Core philosophy

- Challenge ambiguous, complex, or risky requests; suggest better alternative. Don't follow blindly.
- Maintainability first; KISS & YAGNI; consistency over novelty; self-documenting code, type hints everywhere, comments only for non-obvious _why_.

## Stack

- **Backend**: Django 6 + DRF, Python 3.14, uv.
- **Frontend**: Vue 3 + Quasar + Pinia + Inertia + Vite + TS + `@sentry/vue`, yarn 4; source in `vue/src/`, tooling at repo root.
- **Jobs / DB / Storage**: huey; MySQL in prod + dev, SQLite in-memory for tests; S3 (UGent endpoint).
- English only (no translations).

## Commands

All backend commands via `./run` (loads `.env`); never call `uv` / `pytest` / `python manage.py` directly. Frontend via `yarn` from the repo root (`corepack enable` once).

## Commit conventions

Conventional Commits: `type(scope): description` — imperative, lowercase, no trailing period, one line, no attribution trailers. Types: `feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `perf`. Breaking: `feat!:` / `BREAKING CHANGE:` footer. Never vague (`wip`, `update`).

## Git workflow

- Branch + PR for sensitive areas — auth / login / sessions, permissions / access control, serializers / API schemas, payments / billing, security settings / secrets handling, CI workflows (`.github/workflows/`) — or when in doubt. Decide before the first commit; a direct-to-`main` change that grows into a sensitive area moves to a branch before committing.
- Everything else (copy, styling, docs, tests, isolated bug fixes, dependency bumps) may go straight to `main`.
- Branch `type/short-description` from `main`; PR title in Conventional Commits form (becomes the squash commit). Never merge your own PR; leave it for review.
- This decides _where_ commits go, not _whether_: commit / push / open PRs only when asked.

## Specs

`openspec/specs/` is source of truth for behaviour; spec-driven changes via OpenSpec (`openspec/changes/`).

## Python

- PEP 8; type hints on all signatures.
- Docstrings (public functions/methods/modules): reST, no type info; `:param` / `:returns` / `:raises` end with period.
- `./run ruff format . && ./run ruff check evan` clean before commit (CI enforces); config in `pyproject.toml`; no inline ignores without justification comment.
- All new code needs tests, in `tests/` (never inline); factories (factory-boy) in `tests/_factories/`, fixtures in `tests/conftest.py` — reuse. Suite: `./run pytest` (coverage on by default).
- Mock/guard filesystem + external services (S3, payments, mail); never production DB or live APIs.

### Test-review workflow

1. Read tests first; fix weak assertions before running.
2. Run adjusted suite — failure after adjustment = real bug.
3. Fix production code; never weaken a test to force green.

## Django

- Fat models, thin views; business logic in models/managers, cross-model ops in `evan/services/`. `select_related` / `prefetch_related` against N+1; `values()` for few columns. Raw SQL only if ORM can't; then parameterised, never string interpolation.
- Never edit shipped migration — new via `./run python manage.py makemigrations evan`; data migrations in own file, reversible where possible. Drift check: `./run python manage.py makemigrations --check evan`.

### API (DRF)

- Under `/api/v1/` (URL-prefix versioning); every viewset registered in `evan/api/routers.py`, explicit `basename`.
- ISO 8601 UTC dates, ISO 3166-1 alpha-2 country codes, decimals as numbers; errors `{"detail": "..."}`.

### Test patterns

- Markers: `api` (API tests), `site` (site/Django-view tests). `api_client` fixture enforces CSRF.
- Suffixes: `_permissions.py` (access by role), `_api.py` (API behaviour); no suffix = model/service/mixed.
- Permission tests via inheritance: `TestForAnonymous` defines full `expected_status_codes` + endpoint tests; `TestForAuthenticated` subclasses it, calls `api_client.force_authenticate(...)` in autouse fixture; role classes (`TestForAttendee`, `TestForEventManager`, `TestForAdmin` / `TestForSuperuser`) override status codes only.
- Naming: `TestJobCreate` / `TestCouponValidation` behaviour, `TestJobSerializer` serializers.

## TypeScript

- TS mandatory, no plain JS; no `any` without justification comment; `unknown` + type guards for untrusted input; `strict`; never relax `tsconfig.json` flags — fix code.
- `interface` for extensible object shapes, `type` for unions / mapped types.
- Prettier + ESLint (`eslint.config.js`, `.prettierrc`); editor defaults in `.editorconfig`.
- All new code needs tests, in `__tests__/<Name>.test.ts` next to the module (vitest `include`); mock external APIs / HTTP, never hit backend; test behaviour, not internals. Coverage v8; config `vite.config.ts`.

## Vue

- `<script setup lang="ts">` mandatory; no Options API, no `defineComponent({})` unless feature requires it.
- Block order: `<style>` → `<template>` → `<script setup lang="ts">`. `PascalCase.vue` components, `useSomething.ts` composables.
- Pinia only for state. Quasar components + utility classes over native HTML / custom CSS.
- Inertia (`@inertiajs/vue3`): Django picks the page component and provides props.
- `shallowRef` for API data, replace `.value` wholesale; `readonly()` for composable output. Complex logic out of `<script setup>`: pure fns in `vue/src/utils/` (no Vue imports), stateful in `vue/src/composables/`.
- No API-calling logic in components — Pinia store or composable. No backend Python types — TS types in `vue/src/types/`.
- Reusable form inputs/dialogs in `vue/src/components/forms/` — check before building new ones.
- Components: `@vue/test-utils` + happy-dom, mock axios / Inertia router / Quasar plugins; composables called directly.

## Error monitoring (Sentry)

Use the Sentry MCP server to investigate errors proactively when debugging.

- **`regionUrl`**: `https://de.sentry.io`
- **`organizationSlug`**: `ea06`
- **`projectSlugOrId`**: `evan-backend` (backend), `evan-frontend` (Vue)

Prefer **`resolvedInNextRelease`** over `resolved` — fix ships with next deployment.

### Bug fix workflow

Sentry issue reveals a bug not covered by an existing test — add regression test before/alongside the fix:

1. Reproduce first: failing test against current code, confirming root cause.
2. Fix code to pass.
3. Verify no related paths left uncovered.

Never close a Sentry bug without a corresponding regression test.

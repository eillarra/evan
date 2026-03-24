# Evan

[![github-tests-py-badge]][github-tests-py]
[![codecov-badge]][codecov]
[![license-badge]](LICENSE)


## Backend

The Evan api/website uses [Django][django] and the [Django REST Framework][drf].

### Install the dependencies

The application uses [uv][uv] to manage application dependencies.

```bash
uv sync --upgrade --group dev
```

### Run the app in development mode

```bash
python manage.py runserver
```

### Run Huey worker

```bash
python manage.py run_huey
```

### Run the tests

```bash
pytest --cov=evan --cov-report=term
```

### Style guide

Tab size is 4 spaces. Max line length is 120. You should run `ruff` before committing any change.

```bash
ruff format . && ruff check evan
```

## Frontend

Some parts of the website are developed as one page applications with [Vue][vue] (`vue` folder).
When working on these, it is necessary to start a node server in parallel, so Django can access the
modules via [Inertia][inertia].

```bash
yarn
yarn dev
```


[codecov]: https://app.codecov.io/gh/eillarra/evan
[codecov-badge]: https://codecov.io/gh/eillarra/evan/graph/badge.svg?token=wsvdcCF75L
[github-tests-py]: https://github.com/eillarra/evan/actions/workflows/tests_py.yml
[github-tests-py-badge]: https://github.com/eillarra/evan/actions/workflows/tests_py.yml/badge.svg?branch=main
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg

[django]: https://www.djangoproject.com/
[drf]: https://www.django-rest-framework.org/
[inertia]: https://inertiajs.com/
[uv]: https://github.com/astral-sh/uv
[vue]: https://vuejs.org/

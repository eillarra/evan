Evan
====

[![github-actions-badge]][github-actions]
[![codecov-badge]][codecov]
[![codefactor-badge]][codefactor]
[![license-badge]](LICENSE)


## Backend

The Evan api/website uses [Django][django] and the [Django REST Framework][drf].

### Application dependencies

The application uses [Pipenv][pipenv] to manage Python packages. While in development, you will need to install
all dependencies (includes packages like `debug_toolbar`):

```bash
pipenv install --dev
pipenv shell
```

Update dependencies (and manually update `requirements.txt`):

```bash
pipenv update --dev && pipenv lock && pipenv requirements
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


[codecov]: https://codecov.io/gh/eillarra/evan
[codecov-badge]: https://codecov.io/gh/eillarra/evan/branch/master/graph/badge.svg
[codefactor]: https://www.codefactor.io/repository/github/eillarra/evan
[codefactor-badge]: https://www.codefactor.io/repository/github/eillarra/evan/badge
[github-actions]: https://github.com/eillarra/evan/actions?query=workflow%3A%22tests%22
[github-actions-badge]: https://github.com/eillarra/evan/workflows/tests/badge.svg
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg

[django]: https://www.djangoproject.com/
[drf]: https://www.django-rest-framework.org/
[inertia]: https://inertiajs.com/
[pipenv]: https://docs.pipenv.org/#install-pipenv-today
[vue]: https://vuejs.org/

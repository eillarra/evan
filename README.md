Evan
====

[![github-actions-badge]][github-actions]
[![codecov-badge]][codecov]
[![codefactor-badge]][codefactor]
[![license-badge]](LICENSE)


The Evan api/website uses [Django][django] and the [Django REST Framework][drf].

Application dependencies
------------------------

The application uses [Pipenv][pipenv] to manage Python packages. While in development, you will need to install
all dependencies (includes packages like `debug_toolbar`):

    $ pipenv install --dev
    $ pipenv shell

Update dependencies (and manually update `requirements.txt`):

    $ pipenv update --dev && pipenv lock -r

Running the server
------------------

    $ python manage.py runserver

Running tests
-------------

    $ pytest --cov=evan --cov-report=term

Run Huey worker
---------------

    $ python manage.py run_huey

Style guide
-----------

Tab size is 4 spaces. Max line length is 120. You should run `flake8` and `black` before committing any change.

    $ flake8 evan
    $ black evan


[codecov]: https://codecov.io/gh/eillarra/evan
[codecov-badge]: https://codecov.io/gh/eillarra/evan/branch/master/graph/badge.svg
[codefactor]: https://www.codefactor.io/repository/github/eillarra/evan
[codefactor-badge]: https://www.codefactor.io/repository/github/eillarra/evan/badge
[github-actions]: https://github.com/eillarra/evan/actions?query=workflow%3A%22tests%22
[github-actions-badge]: https://github.com/eillarra/evan/workflows/tests/badge.svg
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg

[django]: https://www.djangoproject.com/
[drf]: https://www.django-rest-framework.org/
[pipenv]: https://docs.pipenv.org/#install-pipenv-today

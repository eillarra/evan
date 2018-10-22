Toucon
======

The Toucon api/website uses [Django](https://www.djangoproject.com/) and
[Django REST framework](http://www.django-rest-framework.org/).

Application dependencies
------------------------
The application uses the [pip Package Manager](http://pip.readthedocs.org/en/latest/) to install dependencies:

    $ pip install -r requirements.txt

Configuration
-------------
For development, create a database and update the `settings/development.py` file.  
Once the database configuration is filled in you can generate the necessary tables and load some fixtures using
`manage.py`:

    $ python manage.py migrate
    $ python manage.py mock

Running the servers
-------------------
    $ python manage.py runserver

Running tests
-------------
    $ coverage run --source='toucon' manage.py test toucon
    $ coverage report -m

Style guide
-----------
Unless otherwise specified, follow
[Django Coding Style](https://docs.djangoproject.com/en/1.11/internals/contributing/writing-code/coding-style/).
Tab size is 4 **spaces**. Maximum line length is 120. All changes should include tests and pass `flake8`.

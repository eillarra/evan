web: gunicorn -b :5000 evan.wsgi:app
worker: celery worker -A evan -n evan --loglevel INFO
beat: celery beat -A evan

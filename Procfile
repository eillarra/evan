web: gunicorn -b :5000 --workers 3 evan.wsgi:app
worker: celery -A evan worker --hostname evan --loglevel INFO
beat: celery -A evan beat

import os


bind = ":5000"
preload_app = True
workers = int(os.environ.get("GUNICORN_WORKERS", 2)) if os.environ.get("DJANGO_ENV") == "production" else 1
worker_class = "gthread"
threads = int(os.environ.get("GUNICORN_THREADS", 8))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 2000))
max_requests_jitter = max_requests // 10

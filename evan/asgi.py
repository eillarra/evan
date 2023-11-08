import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import evan.websockets.urls


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evan.settings")
os.environ["HTTPS"] = "on"
django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(evan.websockets.urls.websocket_urlpatterns)),
    }
)

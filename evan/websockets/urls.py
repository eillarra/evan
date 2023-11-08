from django.urls import path

from .consumers import UserResponseConsumer


websocket_urlpatterns = [
    path("ws/example/", UserResponseConsumer.as_asgi()),
]

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class UserResponseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("user_response_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("user_response_updates", self.channel_name)

    async def receive(self, text_data):
        pass  # Not expecting to receive data from client in this case

    async def send_user_response_update(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

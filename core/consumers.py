import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from core.models import ChatMessage, OnlineUser
from django.utils import timezone
from django.db import models

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.room_group_name = f'user_{self.user.username}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.set_online()
        # Send chat history with each user
        recipient_username = self.scope['url_route']['kwargs'].get('recipient')
        if recipient_username:
            history = await self.get_history(recipient_username)
            await self.send(text_data=json.dumps({'history': history}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.set_offline()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        recipient_username = data.get('recipient')
        sender = self.user.username
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        # Save message
        await self.save_message(sender, recipient_username, message, timestamp)
        # Send to recipient and sender only
        for username in set([recipient_username, sender]):
            await self.channel_layer.group_send(
                f'user_{username}',
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': sender,
                    'timestamp': timestamp,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user'],
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def save_message(self, sender_username, recipient_username, content, timestamp):
        sender = User.objects.get(username=sender_username)
        recipient = User.objects.get(username=recipient_username)
        ChatMessage.objects.create(sender=sender, recipient=recipient, content=content, timestamp=timestamp)

    @sync_to_async
    def get_history(self, recipient_username):
        recipient = User.objects.get(username=recipient_username)
        messages = ChatMessage.objects.filter(
            (models.Q(sender=self.user, recipient=recipient) | models.Q(sender=recipient, recipient=self.user))
        ).order_by('timestamp')
        return [
            {
                'user': msg.sender.username,
                'message': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for msg in messages
        ]

    @sync_to_async
    def set_online(self):
        OnlineUser.objects.update_or_create(user=self.user)
    @sync_to_async
    def set_offline(self):
        OnlineUser.objects.filter(user=self.user).delete() 
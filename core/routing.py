from django.urls import re_path
from core import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<recipient>\w+)/$', consumers.ChatConsumer.as_asgi()),
] 
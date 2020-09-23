from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/play/(?P<game_uid>[0-9a-z]{12})/$', consumers.PlayConsumer),
]

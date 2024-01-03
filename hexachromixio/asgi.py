"""
ASGI config for hexachromixio project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from hexachromix.routing import websocket_urlpatterns

import logging
logger = logging.getLogger(__name__)
logger.warn('...in asgi.py...')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hexachromixio.settings')
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

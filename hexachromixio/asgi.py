"""
ASGI config for hexachromixio project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os, django

from channels.routing import get_default_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hexachromixio.settings')

django.setup()

# https://stackoverflow.com/questions/59908273/django-daphne-asgi-django-can-only-handle-asgi-http-connections-not-websocket
application = get_default_application()

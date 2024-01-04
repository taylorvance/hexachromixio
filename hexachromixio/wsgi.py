"""
WSGI config for hexachromixio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hexachromixio.settings')

from django.core.wsgi import get_wsgi_application

# import logging
# logger = logging.getLogger(__name__)
# logger.warn('...in wsgi.py...')

application = get_wsgi_application()

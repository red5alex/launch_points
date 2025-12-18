"""
ASGI config for launch_points_web project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'launch_points_web.settings.development')

application = get_asgi_application()


"""
WSGI config for launch_points_web project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'launch_points_web.settings.development')

application = get_wsgi_application()


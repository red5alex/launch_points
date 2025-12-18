"""
Development settings - uses Spatialite (SQLite with spatial extensions).
"""
from .base import *

# Database - Spatialite (SQLite with spatial extensions)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug settings
DEBUG = True

# Email backend (console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


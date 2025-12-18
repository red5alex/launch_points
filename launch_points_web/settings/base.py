"""
Base settings for Launch Points Web application.
"""
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # GeoDjango
    'rest_framework',  # Django REST Framework
    'rest_framework_gis',  # DRF GIS
    'corsheaders',  # CORS headers
    'core',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware (before CommonMiddleware)
    'django.middleware.locale.LocaleMiddleware',  # i18n middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'launch_points_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # i18n context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'launch_points_web.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('de', 'Deutsch'),
]
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# CORS settings (adjust for production)
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all origins in debug mode
CORS_ALLOWED_ORIGINS = []  # Add specific origins in production

# GeoDjango settings
# Auto-detect conda environment paths if available
_conda_prefix = os.environ.get('CONDA_PREFIX', '')
if _conda_prefix:
    _gdal_path = os.path.join(_conda_prefix, 'Library', 'bin', 'gdal.dll')
    _geos_path = os.path.join(_conda_prefix, 'Library', 'bin', 'geos_c.dll')
    if os.path.exists(_gdal_path):
        GDAL_LIBRARY_PATH = _gdal_path
    else:
        GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', '')
    if os.path.exists(_geos_path):
        GEOS_LIBRARY_PATH = _geos_path
    else:
        GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH', '')
else:
    GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', '')
    GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH', '')


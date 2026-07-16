"""
Configuración del microservicio de facturación multi-tenant.
Credenciales sensibles se leen de variables de entorno.
"""
import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(os.environ.get(key, default)).lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY    = env('SECRET_KEY', 'dev-insecure-change-me-in-production')
DEBUG         = env_bool('DEBUG', False)
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS', '').split(',') if h.strip()] or ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'facturacion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'sri_service.urls'
WSGI_APPLICATION = 'sri_service.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

_db_url = env('DATABASE_URL', '')
if _db_url:
    _u = urllib.parse.urlparse(_db_url)
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     _u.path.lstrip('/'),
            'USER':     _u.username or '',
            'PASSWORD': _u.password or '',
            'HOST':     _u.hostname or 'localhost',
            'PORT':     str(_u.port or 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     env('DB_NAME', 'sri_facturacion'),
            'USER':     env('DB_USER', 'postgres'),
            'PASSWORD': env('DB_PASSWORD', ''),
            'HOST':     env('DB_HOST', 'localhost'),
            'PORT':     env('DB_PORT', '5432'),
        }
    }

LANGUAGE_CODE = 'es-ec'
TIME_ZONE     = 'America/Guayaquil'
USE_TZ        = True

STATIC_URL  = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Directorio donde se guardan los XMLs y PDFs por contribuyente
COMPROBANTES_DIR = env('COMPROBANTES_DIR', str(BASE_DIR / 'comprobantes'))

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['facturacion.auth.ApiKeyAuthentication'],
    'DEFAULT_PERMISSION_CLASSES':     ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES':       ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES':         ['rest_framework.parsers.JSONParser'],
}

# Celery
CELERY_BROKER_URL        = env('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND    = env('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TIMEZONE          = TIME_ZONE

# Email
EMAIL_BACKEND  = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST     = env('EMAIL_HOST', '')
EMAIL_PORT     = int(env('EMAIL_PORT', '587'))
EMAIL_USE_TLS  = env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER     = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = env('DEFAULT_FROM_EMAIL', 'noreply@sri-facturacion.local')

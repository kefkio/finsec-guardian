import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'scanner',
    'threats',
    'audit',
    'records',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
}

CORS_ALLOW_ALL_ORIGINS = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = True

# ---------------------------------------------------------------------------
# Analysis tool configuration
#
# Each entry maps a tool name to either:
#   - the path to a Python interpreter in a dedicated virtualenv (Mythril)
#   - the path to a standalone binary (Echidna)
#
# If an entry is omitted the runner falls back to the tool's default binary
# on the system PATH (e.g. 'myth', 'echidna').
#
# Example:
#   ANALYSIS_TOOL_VENVS = {
#       'mythril':  '/opt/venvs/mythril/bin/python',
#       'echidna':  '/usr/local/bin/echidna',
#   }
# ---------------------------------------------------------------------------
ANALYSIS_TOOL_VENVS = {
    # 'mythril':  os.environ.get('MYTHRIL_PYTHON', ''),
    # 'echidna':  os.environ.get('ECHIDNA_BINARY', ''),
}

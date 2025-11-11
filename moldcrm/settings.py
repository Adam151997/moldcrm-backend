"""
Django settings for moldcrm project - FINAL VERSION
"""
import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-final-fix-67890')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',  # KEEP THIS
    'accounts',
    'users',
    'crm',
    'custom_objects',
    'api',
]

# 🚨 CRITICAL: ADD CORS MIDDLEWARE AT THE TOP
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 🚨 ADD THIS - MUST BE FIRST
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'moldcrm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'moldcrm.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:LTUuBazqwpjrYvMRFBRjsnWxzfXhDwsA@maglev.proxy.rlwy.net:40335/railway',
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  # 🚨 CHANGE TO TokenAuthentication
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# 🚨 CRITICAL: UPDATE CORS SETTINGS
CORS_ALLOWED_ORIGINS = [
    "https://moldcrm-frontend.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 🚨 ADD THESE FOR DEVELOPMENT
CORS_ALLOW_ALL_ORIGINS = True  # Remove in production
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://moldcrm-backend-moldcrm-backend.up.railway.app",
    "https://moldcrm-frontend.vercel.app",  # 🚨 ADD FRONTEND
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
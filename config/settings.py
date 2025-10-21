"""
Full Django settings.py configured for:
- Deploy on Render (free tier)
- Database: Supabase Postgres
- Media (uploads): Supabase Storage (S3-compatible) -> bucket `images`
- Static files: WhiteNoise (served by Django) for Render

IMPORTANT: Replace environment variables in your Render Dashboard. Do NOT commit secrets to git.

Environment variables expected:
- DJANGO_SECRET_KEY
- DEBUG ("True"/"False")
- ALLOWED_HOSTS (comma-separated)
- SUPABASE_DB_URL           -> full postgres URL (from Supabase 'Connection string')
- SUPABASE_S3_KEY          -> S3 Access Key ID (Storage -> Settings -> S3 keys)
- SUPABASE_S3_SECRET       -> S3 Secret Access Key
- SUPABASE_PROJECT_REF     -> your Supabase project ref (the 8+ char prefix in your supabase url)
- SUPABASE_BUCKET_NAME     -> images
- SUPABASE_S3_REGION       -> region (copy from project settings, e.g. 'us-east-1')

Packages to install (pip):
- django
- gunicorn
- dj-database-url
- django-storages[boto3]
- boto3
- whitenoise

Save this file as config/settings.py (you said deploy uses config/settings.py)
"""

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Basic secrets from env
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-dev-secret')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()] or ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'finance_dashboard',
    'widget_tweaks',


    # third-party
    'storages',
    # your apps
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database: use SUPABASE_DB_URL (Postgres) via dj_database_url
DATABASE_URL = os.environ.get('SUPABASE_DB_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise config (serves static on Render)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media (user uploads) - configure to use Supabase S3-compatible storage via django-storages
# Expected envs
SUPABASE_S3_KEY = os.environ.get('SUPABASE_S3_KEY')
SUPABASE_S3_SECRET = os.environ.get('SUPABASE_S3_SECRET')
SUPABASE_PROJECT_REF = os.environ.get('SUPABASE_PROJECT_REF')
SUPABASE_BUCKET_NAME = os.environ.get('SUPABASE_BUCKET_NAME', 'images')
SUPABASE_S3_REGION = os.environ.get('SUPABASE_S3_REGION', 'us-east-1')

# If all S3 creds present, use S3Boto3Storage backend
if SUPABASE_S3_KEY and SUPABASE_S3_SECRET and SUPABASE_PROJECT_REF:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID = SUPABASE_S3_KEY
    AWS_SECRET_ACCESS_KEY = SUPABASE_S3_SECRET
    AWS_STORAGE_BUCKET_NAME = SUPABASE_BUCKET_NAME

    # S3 endpoint for Supabase (S3 compatible)
    # Example: https://xyzabcdw.supabase.co/storage/v1
    AWS_S3_ENDPOINT_URL = f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1"
    AWS_S3_REGION_NAME = SUPABASE_S3_REGION

    # Ensure signature v4
    AWS_S3_SIGNATURE_VERSION = 's3v4'

    # Make uploaded media files publicly readable by default (you can change)
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False

    # Optional: set custom domain if using CDN
    AWS_S3_CUSTOM_DOMAIN = None

    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/object/{SUPABASE_BUCKET_NAME}/"
    MEDIA_ROOT = ''
else:
    # Fallback to local media (only for local dev)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging (simple)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Helpful tips printed at startup (optional)
print('\n--- Django startup: using Supabase S3 storage' if SUPABASE_S3_KEY and SUPABASE_S3_SECRET else '\n--- Django startup: using local storage')

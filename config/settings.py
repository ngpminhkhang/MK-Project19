"""
Django settings for config project.
BẢN NÂNG CẤP GIAI ĐOẠN 4: LẮP ỐNG XẢ TURBO (REAL-TIME PIPELINE)
"""

import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv
import logging

# Chặn họng bọn log tào lao để tập trung vào rủi ro
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-h8a$#1$rg)-n@4uqhcykr6ck6^x1fpun)+f3n+gj6o4x7qp88t')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ["*"]

# ==========================================
# CẤU HÌNH APPS (DAPHNE PHẢI NẰM ĐẦU)
# ==========================================
INSTALLED_APPS = [
    #'daphne',  # Trình duyệt WebSocket bọc thép - Phải nằm đầu tiên
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'channels',      # Động cơ WebSocket
    'corsheaders',   # Cầu nối cho React/Tauri
    'widget_tweaks', # Làm đẹp Form
    'finance_dashboard', # Đại bản doanh
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Giao thức truyền tin: WSGI cho HTTP, ASGI cho WebSocket
WSGI_APPLICATION = 'config.wsgi.application'
#ASGI_APPLICATION = 'config.asgi.application'

# ==========================================
# HỆ THỐNG DẪN DẦU (DATABASE & CACHE)
# ==========================================
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://neondb_owner:npg_k8QAvcIrX5NR@ep-muddy-salad-a1kqe07o-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require',
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Redis: Trạm trung chuyển dữ liệu thời gian thực
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', ("127.0.0.1", 6379))],
        },
    },
}

# Celery: Lính tuần tra ngầm (Quét Drawdown/Exposure mỗi giây)
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Cache hệ thống dùng chung Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ==========================================
# CẤU HÌNH AN NINH & TÀI KHOẢN
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/portfolio/'
LOGOUT_REDIRECT_URL = '/'

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "http://localhost:3000"]

# AWS S3: Kho vũ khí hình ảnh (Chỉ dùng khi có lệnh từ Cloud)
if 'AWS_STORAGE_BUCKET_NAME' in os.environ:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-2')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'monitor-risk-every-second': {
        'task': 'finance_dashboard.tasks.monitor_portfolio_risk_task',
        'schedule': 1.0, # Quét mỗi giây một lần
    },
}
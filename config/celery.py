import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Cấu hình đặc trị cho Windows
app.conf.update(
    worker_max_tasks_per_child=1,
    broker_connection_retry_on_startup=True,
)
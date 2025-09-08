import os
from celery import Celery

# django configuration for celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_api.settings')

app = Celery('sales_api')

# read config from django settings, the CELERY namespace means all celery-related
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto-discover tasks from all registered django app configs
app.autodiscover_tasks()

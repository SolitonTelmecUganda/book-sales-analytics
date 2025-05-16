from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import importlib

app = Celery('datawarehouse')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load dynamic tasks from settings
for task_name, task_config in settings.DATA_SYNC_SCHEDULE.items():
    module_path, func_name = task_config['function'].rsplit('.', 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)

    if task_config['schedule'] == 'interval':
        app.add_periodic_task(
            task_config.get('hours', 24) * 60 * 60,
            func.s(*task_config.get('args', [])),
            name=task_name
        )
    elif task_config['schedule'] == 'cron':
        app.add_periodic_task(
            crontab(
                hour=task_config.get('hour', '*'),
                minute=task_config.get('minute', '*')
            ),
            func.s(*task_config.get('args', [])),
            name=task_name
        )
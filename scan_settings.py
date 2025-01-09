from app import app, db
from models import ScanSettings
from celery.schedules import crontab


def get_scan_settings_schedule():
    # Loads frequency settings for schedule form ScanSettings

    schedules = {}
    try:
        print("[INFO] Loading schedule from ScanSettings...")
        with app.app_context():
            settings = ScanSettings.query.all()
            print(f"[DEBUG]  {len(settings)} records found in ScanSettings table.")

            for setting in settings:
                try:
                    if setting.frequency == 'daily':
                        schedules[f'scan-daily-{setting.id}'] = {
                            'task': 'tasks.run_scheduled_scans',
                            'schedule': crontab(hour=7, minute=0),
                            'args': ()
                        }
                    elif setting.frequency == 'weekly':
                        schedules[f'scan-weekly-{setting.id}'] = {
                            'task': 'tasks.run_scheduled_scans',
                            'schedule': crontab(day_of_week='mon', hour=7, minute=0),
                            'args': ()
                        }
                    elif setting.frequency == 'monthly':
                        schedules[f'scan-monthly-{setting.id}'] = {
                            'task': 'tasks.run_scheduled_scans',
                            'schedule': crontab(day_of_month=1, hour=7, minute=0),
                            'args': ()
                        }
                    elif setting.frequency == 'custom' and setting.custom_cron:
                        cron_parts = setting.custom_cron.split(' ')
                        if len(cron_parts) != 5:
                            raise ValueError("Custom cron expression must have exactly 5 fields.")
                        schedules[f'scan-custom-{setting.id}'] = {
                            'task': 'tasks.run_scheduled_scans',
                            'schedule': crontab(
                                minute=cron_parts[0],
                                hour=cron_parts[1],
                                day_of_month=cron_parts[2],
                                month_of_year=cron_parts[3],
                                day_of_week=cron_parts[4]
                            ),
                            'args': (),
                            'options': {'queue': 'celery'}
                        }
                except Exception as e:
                    print(f"[ERROR] Configuration error for setting: {setting.id}: {e}")
    except Exception as e:
        print(f"[ERROR] Error loading schedule from ScanSettings: {e}")

    return schedules

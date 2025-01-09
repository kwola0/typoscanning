import json
import time
from datetime import datetime

from croniter import croniter

from app import app
from models import Domain, ScanSettings, ScanHistory
from report_utils import send_alert_email_with_summary
from scanner import full_scan_domain


def perform_full_scan(domain: Domain):
    try:
        print(f"[INFO] Performing full scan for domain: {domain.name}")
        full_scan_domain(domain)
        print(f"[SUCCESS] Full scan completed for domain: {domain.name}")
    except Exception as e:
        print(f"[ERROR] Error during full scan for domain {domain.name}: {e}")


def run_scheduled_scans(db):
    with app.app_context():
        scans_with_alerts = []
        settings = ScanSettings.query.all()
        now = datetime.utcnow()

        print(f"[DEBUG] Current time: {now}")
        print("[DEBUG] Retrieved scan settings from the database:")

        for setting in settings:
            session = db.session
            domain = session.get(Domain, setting.domain_id)
            if not domain:
                print(f"[WARNING] Domain with ID {setting.domain_id} not found.")
                continue

            print(f"[DEBUG] Domain: {domain.name}, Frequency: {setting.frequency}, Custom Cron: {setting.custom_cron}")

            scan_performed = False

            if setting.frequency == 'daily' and now.hour == 7 and now.minute == 0:
                print(f"[INFO] Triggering daily scan for domain: {domain.name}")
                perform_full_scan(domain)
                scan_performed = True
            elif setting.frequency == 'weekly' and now.weekday() == 0 and now.hour == 7 and now.minute == 0:
                print(f"[INFO] Triggering weekly scan for domain: {domain.name}")
                perform_full_scan(domain)
                scan_performed = True
            elif setting.frequency == 'monthly' and now.day == 1 and now.hour == 7 and now.minute == 0:
                print(f"[INFO] Triggering monthly scan for domain: {domain.name}")
                perform_full_scan(domain)
                scan_performed = True
            elif setting.frequency == 'custom' and setting.custom_cron:
                if check_custom_cron(setting.custom_cron, now):
                    print(f"[INFO] Triggering custom scan for domain: {domain.name}")
                    perform_full_scan(domain)
                    scan_performed = True
            else:
                print(f"[DEBUG] No scan triggered for domain: {domain.name} at this time.")

            # Alert logic
            if scan_performed:
                latest_scan = ScanHistory.query.filter_by(domain_id=domain.id).order_by(ScanHistory.date.desc()).first()
                if latest_scan:
                    alerted_domains = json.loads(latest_scan.domains_alerted) if latest_scan.domains_alerted else []
                    if alerted_domains:
                        scans_with_alerts.append(latest_scan)

        if scans_with_alerts:
            user = scans_with_alerts[0].domain.owner
            print(f"[INFO] Sending summary alert email to {user.email}")
            send_alert_email_with_summary(user, scans_with_alerts)
            print(f"[INFO] Summary alert email sent to {user.email}")
        else:
            print(f"[DEBUG] No alerts detected, no email sent.")


def check_custom_cron(cron_expression, current_time):
    try:
        iter = croniter(cron_expression, current_time)
        previous_run = iter.get_prev(datetime)
        next_run = iter.get_next(datetime)

        print(f"[DEBUG] Cron Previous Run: {previous_run}, Next Run: {next_run}")

        if (previous_run.minute == current_time.minute and
                previous_run.hour == current_time.hour and
                previous_run.day == current_time.day and
                previous_run.month == current_time.month and
                previous_run.year == current_time.year):
            print(f"[DEBUG] Custom cron matched for time: {current_time}")
            return True

        return False
    except Exception as e:
        print(f"[ERROR] Invalid cron expression {cron_expression}: {e}")
        return False


def run_scheduler(db=None):
    from app import app

    print("[INFO] Scheduler started. Checking database for tasks every minute...")
    while True:
        with app.app_context():
            run_scheduled_scans(db)
        time.sleep(60)


if __name__ == '__main__':
    run_scheduler()

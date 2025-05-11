import threading
from app import app, db
from scheduler import run_scheduler
import time


def start_flask():

    print("[INFO] Starting Flask app...")
    app.run(debug=True, use_reloader=False)


def start_scheduler():

    print("[INFO] Starting Scheduler...")
    run_scheduler(db)


if __name__ == '__main__':
    try:

        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()

        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down application and scheduler...")


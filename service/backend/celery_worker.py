from celery import Celery
from db_manager import DatabaseManager
from health_check_only_url import check_url_health
import logging
from email_notifications import send_email
import datetime

logging.basicConfig(level=logging.INFO)
app = Celery('tasks', broker='redis://localhost:6379/0')
app.conf.beat_schedule = {
    'check_all_microservices_every_5_seconds': {
        'task': 'celery_worker.check_all_microservices',
        'schedule': 5.0
    }
}


@app.task
def check_microservice_health(microservice_id, url, service_id):
    db = DatabaseManager('itinfra.db')
    cursor = db.conn.cursor()
    # Извлечение user_email и user_id
    cursor.execute('''
    SELECT u.email, u.user_id
    FROM Users u
    JOIN Services s ON u.user_id = s.user_id
    WHERE s.service_id = ?
    ''', (service_id,))
    result = cursor.fetchone()
    user_email = result[0]
    user_id = result[1]

    status, response_time = check_url_health(url)
    db.save_service_health_check(microservice_id, status, response_time)
    if status == 'down':
        current_time = datetime.now()
        db.save_report_to_db(service_id, 'Service Down', 'Detected a down status', current_time.strftime('%Y-%m-%d'), current_time.strftime('%Y-%m-%d'))
        db.update_service_status_based_on_microservices(service_id)
        send_email("Alert: Microservice Down", f"Microservice {microservice_id} is down at {url}.", user_email, user_id, service_id)
    db.conn.close()


@app.task
def check_all_microservices():
    db = DatabaseManager('itinfra.db')
    cursor = db.conn.cursor()
    cursor.execute('SELECT microservice_id, url FROM Microservices WHERE is_active = 1')
    microservices = cursor.fetchall()
    for microservice_id, url in microservices:
        check_microservice_health.delay(microservice_id, url)
    db.conn.close()

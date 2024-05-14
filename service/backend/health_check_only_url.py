import requests
from db_manager import DatabaseManager


def check_url_health(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        # Будет вызвано исключение, если ответ не 200
        return 'up', response.elapsed.total_seconds()
    except requests.RequestException:
        return 'down', None


def save_health_status(microservice_id, status, response_time):
    db = DatabaseManager('itinfra.db')
    db.save_service_health_check(microservice_id, status, response_time)
    db.close_connection()

import db_manager


def populate_database(db_manager):
    # Добавление пользователей
    users = [
        ('alice', db_manager.hash_password('password1'), 'alice@example.com'),
        ('bob', db_manager.hash_password('password2'), 'bob@example.com')
    ]
    for username, password_hash, email in users:
        db_manager.register_user(username, password_hash, email)

    # Добавление услуг
    services = [
        (1, 'Web Hosting', 'Provides cloud hosting services', True),
        (2, 'Data Analytics', 'Provides data processing services', True)
    ]
    for user_id, service_name, description, is_active in services:
        db_manager.add_service(user_id, service_name, description, is_active)

    # Добавление микросервисов
    microservices = [
        (1, 'User Service', 'http://example.com/api/users', True),
        (1, 'Auth Service', 'http://example.com/api/auth', True),
        (2, 'Data Processing', 'http://example.com/api/data', True),
        (2, 'Data Storage', 'http://example.com/api/storage', True)
    ]
    for service_id, name, url, is_active in microservices:
        db_manager.add_microservice(service_id, name, url, is_active)

    # Настройка запланированных проверок
    scheduled_checks = [
        (1, 300, '2023-01-01T00:05:00'),
        (2, 600, '2023-01-01T00:10:00')
    ]
    for microservice_id, check_interval, next_check_at in scheduled_checks:
        db_manager.add_scheduled_check(microservice_id, check_interval, next_check_at)


populate_database(db_manager.db)

import sqlite3
import bcrypt
import service_linter


class DatabaseManager:
    def __init__(self, db_filename):
        self.conn = sqlite3.connect(db_filename)
        self.linter = service_linter.ServiceLint()
        self.create_tables()

    def create_tables(self):
        queries = [
            '''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Services (
                service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users (user_id)
            )
            ''',
            '''
                    CREATE TABLE IF NOT EXISTS Microservices (
                        microservice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id INTEGER NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        url VARCHAR(255) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES Services (service_id)
                    )
                    ''',
            '''
                    CREATE TABLE IF NOT EXISTS ServiceHealthChecks (
                        healthcheck_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        microservice_id INTEGER NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        response_time FLOAT,
                        checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (microservice_id) REFERENCES Microservices (microservice_id)
                    )''',
            '''
                    CREATE TABLE IF NOT EXISTS ServiceDependencies (
                        dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id INTEGER NOT NULL,
                        microservice_origin_id INTEGER NOT NULL,
                        microservice_target_id INTEGER NOT NULL,
                        FOREIGN KEY (service_id) REFERENCES Services (service_id),
                        FOREIGN KEY (microservice_origin_id) REFERENCES Microservices (microservice_id),
                        FOREIGN KEY (microservice_target_id) REFERENCES Microservices (microservice_id)
                    )''',
            '''
                    CREATE TABLE IF NOT EXISTS Alerts (
                        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES Services (service_id),
                        FOREIGN KEY (user_id) REFERENCES Users (user_id)
                    )''',
            '''
                    CREATE TABLE IF NOT EXISTS Reports (
                        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id INTEGER NOT NULL,
                        period_start DATE,
                        period_end DATE,
                        report_data BLOB,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES Services (service_id)
                    )''',
            '''
                    CREATE TABLE IF NOT EXISTS ScheduledChecks (
                        scheduled_check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        microservice_id INTEGER NOT NULL,
                        check_interval INTEGER NOT NULL,
                        next_check_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (microservice_id) REFERENCES Microservices (microservice_id)
                    )''',

        ]
        for query in queries:
            self.conn.execute(query)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def delete_database(self):
        queries = [
            'DROP TABLE IF EXISTS Users',
            'DROP TABLE IF EXISTS Services',
            'DROP TABLE IF EXISTS Microservices',
            'DROP TABLE IF EXISTS ServiceHealthChecks',
            'DROP TABLE IF EXISTS ServiceDependencies',
            'DROP TABLE IF EXISTS Alerts',
            'DROP TABLE IF EXISTS Reports',
            'DROP TABLE IF EXISTS ScheduledChecks'
        ]
        for query in queries:
            self.conn.execute(query)
        self.conn.commit()

    def close_connection(self):
        self.conn.close()

    def check_password(self, username, password):
        query = "SELECT password_hash FROM Users WHERE username = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        if user:
            return bcrypt.checkpw(password.encode(), user[0])
        return False

    def add_service(self, user_id, service_name, description, is_active=True):
        query = '''
        INSERT INTO Services (user_id, service_name, description, is_active) VALUES (?, ?, ?, ?)
        '''
        self.conn.execute(query, (user_id, service_name, description, is_active))
        self.conn.commit()

    def register_user(self, username, password, email):
        if self.user_exists(username):
            return False
        hashed_password = self.hash_password(password)
        query = "INSERT INTO Users (username, password_hash, email) VALUES (?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, email))
        self.conn.commit()
        return True

    def get_user_by_username(self, username):
        query = '''
        SELECT * FROM Users WHERE username = ?
        '''
        cursor = self.conn.cursor()
        cursor.execute(query, (username,))
        return cursor.fetchone()

    def user_exists(self, username):
        query = "SELECT 1 FROM Users WHERE username = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (username,))
        return cursor.fetchone() is not None

    def hash_password(self, password):
        # Проверяем, необходимо ли кодировать пароль перед хешированием
        if isinstance(password, str):
            password = password.encode()
            # Кодируем только если пароль в виде строки
        return bcrypt.hashpw(password, bcrypt.gensalt())

    def add_microservice(self, service_id, name, url, is_active=True):
        if not self.linter.is_valid_url(url):  # Проверка URL
            raise ValueError(f"Invalid URL provided: {url}")

        try:
            query = '''
            INSERT INTO Microservices (service_id, name, url, is_active) VALUES (?, ?, ?, ?)
            '''
            self.conn.execute(query, (service_id, name, url, is_active))
            self.conn.commit()
        except Exception as e:
            print(f"Failed to add or update microservice: {e}")
            self.conn.rollback()

    def update_microservice(self, microservice_id, **kwargs):
        updates = ', '.join(f"{key} = ?" for key in kwargs)
        values = list(kwargs.values())
        values.append(microservice_id)
        query = f'UPDATE Microservices SET {updates} WHERE microservice_id = ?'
        self.conn.execute(query, values)
        self.conn.commit()

    def update_service(self, service_id, **kwargs):
        updates = ', '.join(f"{key} = ?" for key in kwargs)
        values = list(kwargs.values())
        values.append(service_id)
        query = f'UPDATE Services SET {updates} WHERE service_id = ?'
        self.conn.execute(query, values)
        self.conn.commit()

    def delete_service(self, service_id):
        # Удаление микросервисов, связанных с этой услугой
        self.conn.execute('DELETE FROM Microservices WHERE service_id = ?', (service_id,))
        # Удаление самой услуги
        self.conn.execute('DELETE FROM Services WHERE service_id = ?', (service_id,))
        self.conn.commit()

    def delete_microservice(self, microservice_id):
        self.conn.execute('DELETE FROM Microservices WHERE microservice_id = ?', (microservice_id,))
        self.conn.commit()

    def save_service_health_check(self, microservice_id, status, response_time):
        query = '''
        INSERT INTO ServiceHealthChecks (microservice_id, status, response_time, checked_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        self.conn.execute(query, (microservice_id, status, response_time))
        self.conn.commit()
        print(f"Logged health check for microservice {microservice_id}: {status}, response time: {response_time}")

    def add_scheduled_check(self, microservice_id, check_interval, next_check_at):
        query = '''
        INSERT INTO ScheduledChecks (microservice_id, check_interval, next_check_at) VALUES (?, ?, ?)
        '''
        self.conn.execute(query, (microservice_id, check_interval, next_check_at))
        self.conn.commit()

    def save_report(self, service_id, report_data, description):
        query = '''
        INSERT INTO Reports (service_id, report_data, description, period_start, period_end, created_at)
        VALUES (?, ?, ?, CURRENT_DATE, CURRENT_DATE, CURRENT_TIMESTAMP)
        '''
        self.conn.execute(query, (service_id, report_data, description))
        self.conn.commit()

    def add_service_dependency(self, service_id, microservice_origin_id, microservice_target_id):
        query = '''
        INSERT INTO ServiceDependencies (service_id, microservice_origin_id, microservice_target_id)
        VALUES (?, ?, ?)
        '''
        self.conn.execute(query, (service_id, microservice_origin_id, microservice_target_id))
        self.conn.commit()

    def save_report_to_db(self, service_id, report_data, start_date, end_date):
        print('reporting')
        query = '''
        INSERT INTO Reports (service_id, report_data, period_start, period_end)
        VALUES (?, ?, ?, ?)
        '''
        self.conn.execute(query, (service_id, report_data, start_date, end_date))
        self.conn.commit()

    def update_service_status_based_on_microservices(self, service_id):
        from email_notifications import send_email

        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT u.email
        FROM Users u
        JOIN Services s ON u.user_id = s.user_id
        WHERE s.service_id = ?
        ''', (service_id,))
        user_email = cursor.fetchone()[0]

        cursor.execute('''
        SELECT microservice_id, is_active FROM Microservices WHERE service_id = ?
        ''', (service_id,))
        microservices = cursor.fetchall()

        # Проверяем, все ли микросервисы активны
        all_active = all(m[1] == 1 for m in microservices)
        if not all_active and len(microservices) > 0:
            # Если хотя бы один микросервис неактивен, услуга считается неактивной
            self.conn.execute('UPDATE Services SET is_active = 0 WHERE service_id = ?', (service_id,))
            self.conn.commit()
            send_email("Alert: Service Down", f"Service {service_id} is down due to inactive microservices.",
                       user_email)
        elif all_active:
            self.conn.execute('UPDATE Services SET is_active = 1 WHERE service_id = ?', (service_id,))
            self.conn.commit()

    def log_alert(self, user_id, service_id, message):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO Alerts (service_id, user_id, message, sent_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (service_id, user_id, message))
        self.conn.commit()


if __name__ == "__main__":
    db = DatabaseManager('itinfra.db')

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime


def generate_service_report(service_id, start_date, end_date):
    from db_manager import DatabaseManager
    conn = sqlite3.connect('itinfra.db')
    cursor = conn.cursor()
    query = '''
        SELECT checked_at, status FROM ServiceHealthChecks
        WHERE microservice_id IN (SELECT microservice_id FROM Microservices WHERE service_id = ?)
        AND checked_at BETWEEN ? AND ?
        '''
    cursor.execute(query, (service_id, start_date, end_date))
    results = cursor.fetchall()

    dates = [datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') for result in results]
    statuses = [1 if result[1] == 'up' else 0 for result in results]

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.plot(dates, statuses, marker='o', linestyle='-', color='b')
    ax.set_title('Service Health Report')
    ax.set_xlabel('Time')
    ax.set_ylabel('Status (1=Up, 0=Down)')

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))

    for date, status in zip(dates, statuses):
        if status == 0:
            text_position = (0, -15)  # Ниже точки
        else:
            text_position = (0, 10)  # Выше точки
        ax.annotate(date.strftime('%Y-%m-%d %H:%M:%S'), (date, status), textcoords="offset points",
                    xytext=text_position, ha='center')

    plt.xticks(rotation=90)  # Поворот меток на 90 градусов
    plt.grid(True)
    plt.tight_layout()

    current_time = datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    plt.savefig(f"../reports/{formatted_time}.png")

    db = DatabaseManager('itinfra.db')
    db.save_report_to_db(service_id, formatted_time, start_date, end_date)


generate_service_report(1, '2023-01-01', '2025-01-02')

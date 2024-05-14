import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject, message, to_email, user_id, service_id):
    from db_manager import DatabaseManager
    sender_email = "my_mail@gmail.com"
    sender_password = "my_password"
    # Здесь необходимо заменить на наши креденциалы

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
        db = DatabaseManager('itinfra.db')
        db.log_alert(user_id, service_id, message)
        db.close()
    except Exception as e:
        print(f"Failed to send email: {e}")

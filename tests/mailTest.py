import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import app

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

EMAIL_ADDRESS = 'typosquattingtest@gmail.com'
EMAIL_PASSWORD=app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

RECIPIENT_EMAIL = 'typosquattingtest@gmail.com'
SUBJECT = 'Test Email from Console'
BODY = 'This is a test email sent from a standalone Python script using Gmail SMTP.'


def send_email():
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = SUBJECT

        msg.attach(MIMEText(BODY, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("[INFO] Sending email...")
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        server.quit()

        print("[SUCCESS] Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Authentication failed. Check your email and App Password.")
    except smtplib.SMTPConnectError:
        print("[ERROR] Failed to connect to the SMTP server.")
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error occurred: {e}")
    except Exception as e:
        print(f"[ERROR] General error occurred: {e}")

if __name__ == '__main__':
     send_email()
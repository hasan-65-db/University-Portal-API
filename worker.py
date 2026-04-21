import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from celery import Celery
from pydantic_settings import BaseSettings
from database import SessionLocal
import models


class Worker_Settings(BaseSettings):
    SENDER_EMAIL:str
    SENDER_PASSWORD:str

    class Config:
        env_file = ".env"
        extra = "ignore"

worker_settings = Worker_Settings()

celery_app = Celery("tasks", broker = os.environ.get("CELERY_BROKER_URL"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

@celery_app.task
def send_registration_email(student_email, course_name):
    try:
        message = MIMEMultipart()
        message["FROM"] = worker_settings.SENDER_EMAIL
        message["TO"] = student_email
        message["SUBJECT"] = f"Enrollment Confirmed: {course_name}"
        body = f"Hello! You have successfully registered for {course_name}."
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(worker_settings.SENDER_EMAIL, worker_settings.SENDER_PASSWORD)
            server.send_message(message)
            return f"Email sent to {student_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}" 

@celery_app.task
def clean_name(student_id: int):
    db = SessionLocal()
    try:
        student = db.query(models.Student).filter(models.Student.id==student_id).first()
        if student:
            cleaned_name = student.name.strip().title()
            if student.name != cleaned_name:
             student.name = cleaned_name
             db.commit()

    except Exception as e:
        db.rollback()
        return f"No cleaning needed for ID {student_id}"

    finally:
        db.close()









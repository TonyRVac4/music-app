import asyncio
import email

import smtplib
from celery.schedules import crontab

from api.src.celery_app import app
from api.src.infrastructure.app import app as app_container
from api.src.infrastructure.settings import settings


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every Sunday morning at 1:00 a.m. UTC
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week=7),
        delete_expired_tokens.s(),
        name="delete_expired_tokens",
    )


@app.task
def delete_expired_tokens():
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # в случае запуска внутри already running loop
        loop.create_task(app_container.auth_service.delete_expired_refresh_tokens())
    else:
        loop.run_until_complete(app_container.auth_service.delete_expired_refresh_tokens())


@app.task
def send_email(to_email: str, message: str) -> None:
    with smtplib.SMTP("smtp.gmail.com", 587) as smtpObj:
        smtpObj.starttls()
        smtpObj.login(
            user=settings.email_client.email, password=settings.email_client.password,
        )
        m = email.message.Message()
        m["From"] = settings.email_client.email
        m["To"] = to_email
        m["Subject"] = "Music App email verification."

        m.set_payload(message)
        smtpObj.sendmail(
            from_addr=settings.email_client.email, to_addrs=to_email, msg=m.as_string(),
        )

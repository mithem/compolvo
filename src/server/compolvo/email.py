import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sanic.log import logger

SMTP: smtplib.SMTP | None = None
SMTP_SENDER: str | None = None


def setup_smtp_server():
    global SMTP, SMTP_SENDER
    host = os.environ.get("SMTP_SERVER")
    port_str = os.environ.get("SMTP_PORT")
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    SMTP_SENDER = os.environ.get("SMTP_SENDER")
    if host is None or port_str is None or username is None or password is None or SMTP_SENDER is None:
        logger.warning("Not enough configuration values for SMTP server configuration")
        SMTP = None
        SMTP_SENDER = None
        return
    port = int(port_str)
    SMTP = smtplib.SMTP_SSL(host, port)
    SMTP.login(username, password)
    logger.info("Logged in to SMTP server successfully")


def quit_smtp_server():
    global SMTP
    if SMTP is not None:
        SMTP.quit()
        SMTP = None


def _get_email_body(template: str, email: str, template_vars: Dict[str, str] | None = None) -> str:
    env = Environment(loader=FileSystemLoader("email/templates"), autoescape=select_autoescape())
    template = env.get_template(template)
    no_tls = os.environ.get("HOSTNAME_TLS", "true").lower() == "false"
    scheme = "http" if no_tls else "https"
    templ_vars = {
        "compolvo_url": f"{scheme}://{os.environ['HOSTNAME']}",
        "email": email,
        **(template_vars if template_vars is not None else {})
    }
    content = template.render(**templ_vars)
    return content


def send_email(email: str, subject: str, template: str,
               template_vars: Dict[str, str] | None = None):
    if SMTP is None or SMTP_SENDER is None:
        logger.warning("SMTP server not set up")
        return
    body = _get_email_body(template, email, template_vars)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_SENDER
    msg["To"] = email

    part = MIMEText(body, "html")
    msg.attach(part)

    logger.info("Sending email to %s", email)
    content = msg.as_string()
    SMTP.sendmail(SMTP_SENDER, email, content)

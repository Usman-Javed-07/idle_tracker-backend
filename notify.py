import smtplib
from email.message import EmailMessage
from backend.config import SMTP_CONFIG

def send_email(to_addrs, subject, body):
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]
    msg = EmailMessage()
    msg["From"] = SMTP_CONFIG["from_addr"]
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
        if SMTP_CONFIG.get("use_tls", True):
            server.starttls()
        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        server.send_message(msg)

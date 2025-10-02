import smtplib
from email.message import EmailMessage
from backend.config import SMTP_CONFIG
import socket


def send_email(to_addrs, subject, body):
    """
    Sends email with a socket timeout.
    If sending fails or stalls, we swallow the error so the UI never freezes.
    """
    try:
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]
        msg = EmailMessage()
        msg["From"] = SMTP_CONFIG["from_addr"]
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.set_content(body)

        timeout = float(SMTP_CONFIG.get("timeout", 6))
        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=timeout) as server:
            if SMTP_CONFIG.get("use_tls", True):
                try:
                    server.ehlo()
                except Exception:
                    pass
                server.starttls()
                try:
                    server.ehlo()
                except Exception:
                    pass
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            server.send_message(msg)
    except (socket.timeout, smtplib.SMTPException, OSError):
        pass

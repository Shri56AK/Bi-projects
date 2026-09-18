"""
Notification channels. `webhook` and `email` are real implementations that
simply need credentials/URLs supplied via environment variables; they fall
back to a clearly-labelled dry-run print when unconfigured so the engine is
runnable out of the box without secrets.
"""
import os
import json
import smtplib
from email.mime.text import MIMEText

import urllib.request
import urllib.error


def notify_console(alert: dict):
    print(
        f"[ALERT] {alert['metric_name']} = {alert['metric_value']} "
        f"{alert['comparison']} {alert['threshold']}  (rule #{alert['rule_id']})"
    )


def notify_webhook(alert: dict):
    url = os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        print(f"[webhook:dry-run] would POST alert -> {json.dumps(alert)}")
        return
    data = json.dumps(alert).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[webhook] delivered, status={resp.status}")
    except urllib.error.URLError as e:
        print(f"[webhook] delivery failed: {e}")


def notify_email(alert: dict):
    host = os.environ.get("SMTP_HOST")
    to_addr = os.environ.get("ALERT_EMAIL_TO")
    from_addr = os.environ.get("ALERT_EMAIL_FROM", "alerts@example.com")
    if not host or not to_addr:
        print(f"[email:dry-run] would email {to_addr or '<unset>'} -> {json.dumps(alert)}")
        return
    msg = MIMEText(json.dumps(alert, indent=2))
    msg["Subject"] = f"Alert: {alert['metric_name']} breached threshold"
    msg["From"] = from_addr
    msg["To"] = to_addr
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 25))) as server:
        server.send_message(msg)
    print(f"[email] sent to {to_addr}")


CHANNELS = {
    "console": notify_console,
    "webhook": notify_webhook,
    "email": notify_email,
}


def dispatch(channel: str, alert: dict):
    fn = CHANNELS.get(channel, notify_console)
    fn(alert)

"""SMTP email sender and Chinese notification templates (M3)."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from app.config import Settings

_LOCAL = ZoneInfo("Asia/Shanghai")


def _fmt(dt) -> str:
    return dt.astimezone(_LOCAL).strftime("%Y-%m-%d %H:%M")


def render(event_type: str, appt, owner_email: str) -> tuple[str, str]:
    """Return (subject, plain_text) for a notification event about ``appt``.

    ``appt`` is a decrypted ``Appointment`` (company_name / meeting_* / contact_* / notes).
    Email is sent to the booking owner (interviewer); candidate-facing Feishu is deferred.
    """

    company = appt.company_name
    window = f"{_fmt(appt.start_at)} – {_fmt(appt.end_at)}"
    contact = f"{appt.contact_last_name}{appt.contact_salutation}（{appt.contact_phone}）"

    if event_type == "appointment_created":
        subject = f"面试预约确认 · {company}"
        body = (
            "你好，以下是面试预约确认信息：\n\n"
            f"公司：{company}\n"
            f"时段：{window}\n"
            f"会议平台：{appt.meeting_platform}\n"
            f"会议号：{appt.meeting_number}\n"
            f"联系人：{contact}\n"
            f"{('备注：' + appt.notes + '\n') if appt.notes else ''}"
            "请准时参加；如有变动请在站点内改期或取消。\n"
        )
    elif event_type == "appointment_cancelled":
        subject = f"（已取消）面试预约 · {company}"
        body = (
            "你好，以下面试预约已取消：\n\n"
            f"公司：{company}\n"
            f"原时段：{window}\n"
            "请重新预约合适时间。\n"
        )
    elif event_type == "appointment_rescheduled":
        subject = f"面试时间已更新 · {company}"
        body = (
            "你好，以下面试时间已更新：\n\n"
            f"公司：{company}\n"
            f"新时段：{window}\n"
            f"会议平台：{appt.meeting_platform}\n"
            f"会议号：{appt.meeting_number}\n"
            "请留意最新时间。\n"
        )
    elif event_type == "appointment_details_updated":
        subject = f"面试信息已更新 · {company}"
        body = (
            "你好，以下面试信息已更新：\n\n"
            f"公司：{company}\n"
            f"时段：{window}\n"
            f"会议平台：{appt.meeting_platform}\n"
            f"会议号：{appt.meeting_number}\n"
            f"联系人：{contact}\n"
            f"{('备注：' + appt.notes + '\n') if appt.notes else ''}"
        )
    elif event_type == "reminder_due":
        subject = f"面试提醒（10 分钟后）· {company}"
        body = (
            "你好，以下面试即将开始：\n\n"
            f"公司：{company}\n"
            f"时段：{window}\n"
            f"会议平台：{appt.meeting_platform}\n"
            f"会议号：{appt.meeting_number}\n"
            "请提前进入会议。\n"
        )
    else:
        subject = f"面试通知 · {company}"
        body = f"公司：{company}\n时段：{window}\n"

    return subject, body


class EmailSender:
    """Send transactional email over SMTP using runtime-only credentials."""

    def __init__(self, settings: Settings) -> None:
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._user = settings.smtp_user
        self._password = settings.smtp_password.get_secret_value() if settings.smtp_password else None
        self._sender = settings.smtp_from or self._user

    def send(self, to: str, subject: str, text: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        with self._connect() as client:
            client.login(self._user, self._password)
            client.send_message(message)

    def _connect(self) -> smtplib.SMTP:
        if self._port == 465:
            return smtplib.SMTP_SSL(self._host, self._port, timeout=10, context=ssl.create_default_context())
        client = smtplib.SMTP(self._host, self._port, timeout=10)
        client.starttls(context=ssl.create_default_context())
        return client

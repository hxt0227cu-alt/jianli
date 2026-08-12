"""SMTP email sender and Chinese notification templates (M3 + M4)."""

from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from app.config import Settings

if TYPE_CHECKING:  # annotations are lazy (PEP 563), so this stays import-cycle free
    from app.appointments.models import Appointment

_LOCAL = ZoneInfo("Asia/Shanghai")


def web_base_url() -> str:
    """Front-end base URL used to build magic-link emails.

    Override per deployment via ``JIANLI_WEB_BASE_URL``; defaults to the local dev
    server. Reads the environment directly (no new Settings field) so M4 stays
    within its approved change surface.
    """

    return os.environ.get("JIANLI_WEB_BASE_URL", "http://localhost:5173")


def _fmt(dt: datetime) -> str:
    return dt.astimezone(_LOCAL).strftime("%Y-%m-%d %H:%M")


def render(event_type: str, appt: Appointment, owner_email: str) -> tuple[str, str]:
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


def render_verification_email(email: str, link: str) -> tuple[str, str]:
    """Return (subject, plain_text) for a new-account email verification link (M4)."""

    subject = "请验证你的简历面试站点邮箱"
    body = (
        f"你好，\n\n感谢注册简历面试站点。请点击以下链接验证邮箱（{email}）：\n"
        f"{link}\n\n"
        "链接 24 小时内有效。如非本人操作，请忽略本邮件。\n"
    )
    return subject, body


def render_reset_email(email: str, link: str) -> tuple[str, str]:
    """Return (subject, plain_text) for a password reset link (M4)."""

    subject = "重置你的简历面试站点密码"
    body = (
        f"你好，\n\n我们收到了重置密码的请求（{email}）。请点击以下链接重置密码：\n"
        f"{link}\n\n"
        "链接 1 小时内有效。如非本人操作，请忽略本邮件，账号仍然安全。\n"
    )
    return subject, body


class EmailSender:
    """Send transactional email over SMTP using runtime-only credentials."""

    def __init__(self, settings: Settings) -> None:
        host, user, password = settings.smtp_host, settings.smtp_user, settings.smtp_password
        if host is None or user is None or password is None:
            # Every call site is guarded by Settings.notification_configured; failing here
            # keeps the missing-credential error at construction instead of mid-send.
            raise ValueError("EmailSender requires SMTP host, user and password")
        self._host: str = host
        self._port: int = settings.smtp_port
        self._user: str = user
        self._password: str = password.get_secret_value()
        self._sender: str = settings.smtp_from or user

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
            return smtplib.SMTP_SSL(
                self._host, self._port, timeout=10, context=ssl.create_default_context()
            )
        client = smtplib.SMTP(self._host, self._port, timeout=10)
        client.starttls(context=ssl.create_default_context())
        return client

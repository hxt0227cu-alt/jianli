"""Feishu channel adapter (R13/R14, TASK-FEISHU-001).

Two capabilities, both callable only from the notification worker (never inside a
database transaction, per architecture §6):

- ``upsert_bitable_row`` — mirror an appointment into the approved Bitable table
  (R14 full view). Idempotent: callers pass the previously stored ``feishu_record_id``
  when they have one (from ``channel_metadata``), otherwise the adapter finds the row
  by the stable 预约ID (appointment UUID) and updates it, creating it only when absent.
- ``send_message`` — plain-text message to a user's open_id (R13 candidate reminder).

The gateway protocol is the extension point: the real implementation talks to the
Feishu OpenAPI over httpx (imported lazily so the dev-only runtime still imports
cleanly); tests inject a stub with the same shape.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.appointments.models import Appointment
from app.config import Settings

_FEISHU_BASE = "https://open.feishu.cn/open-apis"
_TOKEN_URL = f"{_FEISHU_BASE}/auth/v3/tenant_access_token/internal"
_MESSAGE_URL = f"{_FEISHU_BASE}/im/v1/messages"
_SEARCH_URL = (
    f"{_FEISHU_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records/search"
)
_RECORD_URL = (
    f"{_FEISHU_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records/{{record_id}}"
)
_RECORDS_URL = f"{_FEISHU_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records"

# 预约ID is the stable dedup key for R14 mirror rows (appointment UUID as text).
_APPOINTMENT_ID_FIELD = "预约ID"
_STATUS_FIELD = "状态"


def _iso(dt: datetime) -> str:
    """Format an aware datetime as a Bitable datetime cell (ms epoch)."""

    return str(int(dt.timestamp() * 1000))


def bitable_fields(appointment: Appointment) -> dict[str, Any]:
    """Map an appointment onto the approved 11-field 预约记录 table schema (SRS R14)."""

    contact = f"{appointment.contact_last_name}{appointment.contact_salutation}"
    return {
        _APPOINTMENT_ID_FIELD: str(appointment.id),
        "公司": appointment.company_name,
        "时段起": _iso(appointment.start_at),
        "时段止": _iso(appointment.end_at),
        "会议平台": appointment.meeting_platform,
        "会议号": appointment.meeting_number,
        "联系人": contact,
        "联系电话": appointment.contact_phone,
        "备注": appointment.notes or "",
        _STATUS_FIELD: appointment.status,
        "更新时间": _iso(datetime.now()),
    }


class FeishuGateway(Protocol):
    """Extension point: Feishu OpenAPI capabilities used by the notification worker."""

    def upsert_bitable_row(
        self, appointment: Appointment, known_record_id: str | None
    ) -> str:
        """Mirror the appointment row; return the Bitable record_id (idempotent)."""

    def send_message(self, open_id: str, text: str) -> str:
        """Send a plain-text message; return the provider message_id."""


class StubFeishuGateway:
    """In-process fake for tests and offline runs (same shape as the real gateway)."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.messages: list[tuple[str, str]] = []
        self._next_record = 0
        self._next_message = 0

    def upsert_bitable_row(
        self, appointment: Appointment, known_record_id: str | None
    ) -> str:
        if known_record_id and known_record_id in self.rows:
            self.rows[known_record_id] = bitable_fields(appointment)
            return known_record_id
        for record_id, fields in self.rows.items():
            if fields.get(_APPOINTMENT_ID_FIELD) == str(appointment.id):
                self.rows[record_id] = bitable_fields(appointment)
                return record_id
        record_id = f"recstub{self._next_record}"
        self._next_record += 1
        self.rows[record_id] = bitable_fields(appointment)
        return record_id

    def send_message(self, open_id: str, text: str) -> str:
        message_id = f"msgsm{self._next_message}"
        self._next_message += 1
        self.messages.append((open_id, text))
        return message_id


class FeishuAPIGateway:
    """Real Feishu OpenAPI client. httpx is imported lazily (TASK-FEISHU-001 promoted
    it to a runtime dependency; keeping the import local mirrors the LLM gateway)."""

    def __init__(self, settings: Settings) -> None:
        if not settings.feishu_configured:
            raise ValueError("FeishuAPIGateway requires app_id, app_secret and bitable tokens")
        self._app_id: str = settings.feishu_app_id or ""
        self._app_secret: str = settings.feishu_app_secret.get_secret_value()  # type: ignore[union-attr]
        self._app_token: str = settings.feishu_bitable_base_token or ""
        self._table_id: str = settings.feishu_bitable_table_id or ""
        self._timeout: float = settings.feishu_timeout_seconds
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -- token ----------------------------------------------------------------

    def _tenant_access_token(self) -> str:
        """Return a cached tenant_access_token, refreshing when near expiry."""

        if self._token and time.monotonic() < self._token_expires_at - 60:
            return self._token
        import httpx

        response = httpx.post(
            _TOKEN_URL,
            json={"app_id": self._app_id, "app_secret": self._app_secret},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"Feishu token error: {payload.get('code')} {payload.get('msg')}")
        self._token = token
        self._token_expires_at = time.monotonic() + float(payload.get("expire", 7200))
        return token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._tenant_access_token()}"}

    def _check(self, payload: dict[str, Any]) -> None:
        if payload.get("code", 0) != 0:
            raise RuntimeError(f"Feishu API error: {payload.get('code')} {payload.get('msg')}")

    # -- R14 bitable mirror ---------------------------------------------------

    def upsert_bitable_row(
        self, appointment: Appointment, known_record_id: str | None
    ) -> str:
        import httpx

        if known_record_id:
            response = httpx.put(
                _RECORD_URL.format(
                    app_token=self._app_token, table_id=self._table_id, record_id=known_record_id
                ),
                headers=self._headers(),
                json={"fields": bitable_fields(appointment)},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            self._check(payload)
            return payload["data"]["record"]["record_id"]
        existing = self._find_row_by_appointment_id(appointment.id)
        if existing:
            return self.upsert_bitable_row(appointment, existing)
        response = httpx.post(
            _RECORDS_URL.format(app_token=self._app_token, table_id=self._table_id),
            headers=self._headers(),
            json={"fields": bitable_fields(appointment)},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        self._check(payload)
        return payload["data"]["record"]["record_id"]

    def _find_row_by_appointment_id(self, appointment_id: UUID) -> str | None:
        """Search the mirror table by the stable 预约ID field; return record_id or None."""

        import httpx

        response = httpx.post(
            _SEARCH_URL.format(app_token=self._app_token, table_id=self._table_id),
            headers=self._headers(),
            json={
                "filter": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": _APPOINTMENT_ID_FIELD,
                            "operator": "is",
                            "value": [str(appointment_id)],
                        }
                    ],
                }
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        self._check(payload)
        items = payload.get("data", {}).get("items", [])
        return items[0]["record_id"] if items else None

    # -- R13 candidate message -----------------------------------------------

    def send_message(self, open_id: str, text: str) -> str:
        import httpx

        response = httpx.post(
            _MESSAGE_URL,
            params={"receive_id_type": "open_id"},
            headers=self._headers(),
            json={"receive_id": open_id, "msg_type": "text", "content": f'{{"text": "{text}"}}'},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        self._check(payload)
        return payload["data"]["message_id"]

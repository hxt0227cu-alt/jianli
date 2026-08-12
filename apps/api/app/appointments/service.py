from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from app.auth.errors import AuthError
from app.auth.models import Principal
from app.auth.rate_limit import RedisClient

from .crypto import (
    BookingCryptoError,
    BookingSecrets,
    ConfirmationTokens,
    FieldCipher,
    canonical_payload_digest,
)
from .models import Appointment, AppointmentDraft, AppointmentPreview, Slot, SlotSnapshot

_CONSUME_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""
LOCAL_TIME = ZoneInfo("Asia/Shanghai")


class BookingRateLimiter:
    def __init__(self, client: RedisClient, hmac_key: str) -> None:
        key = hmac_key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("rate-limit HMAC key must be at least 32 UTF-8 bytes")
        self._client = client
        self._key = key

    def consume(self, user_id: UUID) -> None:
        account = hmac.new(self._key, str(user_id).encode("ascii"), hashlib.sha256).hexdigest()
        try:
            current, ttl = self._client.eval(
                _CONSUME_SCRIPT, 1, f"booking:create:account:{account}", 3600
            )
        except Exception as error:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limit unavailable",
                "Booking is temporarily unavailable",
                1,
            ) from error
        if int(current) > 10:
            raise AuthError(
                "RATE_LIMITED", 429, "Rate limited", "Try again later", max(int(ttl), 1)
            )


@dataclass(frozen=True, slots=True)
class SlotRow:
    id: UUID
    start_at: datetime
    end_at: datetime
    status: str


class BookingService:
    def __init__(
        self,
        engine: Engine,
        secrets_config: BookingSecrets,
        redis_client: RedisClient,
        rate_limit_key: str,
    ) -> None:
        self._engine = engine
        self._secrets = secrets_config
        self._cipher = FieldCipher(secrets_config.current_key_id, secrets_config.field_keys)
        self._tokens = ConfirmationTokens(secrets_config.confirmation_hmac_key)
        self._rate_limiter = BookingRateLimiter(redis_client, rate_limit_key)

    def slot_snapshot(self, principal: Principal, week_offset: int) -> SlotSnapshot:
        now = datetime.now(UTC)
        local_today = now.astimezone(LOCAL_TIME).date()
        monday = local_today - timedelta(days=local_today.weekday()) + timedelta(weeks=week_offset)
        start_at = datetime.combine(monday, datetime.min.time(), LOCAL_TIME).astimezone(UTC)
        end_at = start_at + timedelta(days=7)
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT s.id,s.start_at,s.end_at,s.status::text AS status,s.version,"
                    "CASE WHEN s.appointment_id IS NULL THEN 'none' "
                    "WHEN a.user_id=:user_id THEN 'self' ELSE 'other' END AS ownership "
                    "FROM appointment_slots s LEFT JOIN appointments a ON a.id=s.appointment_id "
                    "WHERE s.start_at>=:start_at AND s.start_at<:end_at "
                    "ORDER BY s.start_at,s.id"
                ),
                {"user_id": principal.id, "start_at": start_at, "end_at": end_at},
            ).mappings()
            items = [
                Slot(
                    id=row["id"],
                    start_at=row["start_at"],
                    end_at=row["end_at"],
                    status=row["status"],
                    resource_version=row["version"],
                    ownership=row["ownership"],
                )
                for row in rows
            ]
        return SlotSnapshot(
            watermark=max((item.resource_version for item in items), default=0),
            generated_at=now,
            items=items,
        )

    def preview(self, principal: Principal, draft: AppointmentDraft) -> AppointmentPreview:
        token, expires_at = self._tokens.issue(principal.id, canonical_payload_digest(draft))
        return AppointmentPreview(
            confirmation_token=token,
            expires_at=expires_at,
            company_name=draft.company_name,
            recipient_email=principal.email,
            salutation=f"{draft.contact_last_name} {draft.contact_salutation}",
        )

    def create(
        self, principal: Principal, draft: AppointmentDraft, confirmation_token: str
    ) -> Appointment:
        self._rate_limiter.consume(principal.id)
        try:
            self._tokens.verify(confirmation_token, principal.id, canonical_payload_digest(draft))
        except BookingCryptoError as error:
            raise AuthError(
                "CONFIRM_EXPIRED", 409, "Confirmation expired", "Confirm the appointment again"
            ) from error

        fingerprint = self._secrets.company_fingerprint(draft.company_name)
        appointment_id = uuid4()
        company_candidate_id = uuid4()
        now = datetime.now(UTC)
        try:
            with self._engine.begin() as connection:
                company_ciphertext = self._cipher.encrypt(
                    draft.company_name,
                    "companies",
                    "raw_name_ciphertext",
                    company_candidate_id,
                )
                connection.execute(
                    text(
                        "INSERT INTO companies "
                        "(id,normalized_name_fingerprint,raw_name_ciphertext) "
                        "VALUES (:id,:fingerprint,:ciphertext) "
                        "ON CONFLICT (normalized_name_fingerprint) DO NOTHING"
                    ),
                    {
                        "id": company_candidate_id,
                        "fingerprint": fingerprint,
                        "ciphertext": company_ciphertext,
                    },
                )
                company_id = connection.execute(
                    text(
                        "SELECT id FROM companies WHERE normalized_name_fingerprint=:fingerprint "
                        "FOR UPDATE"
                    ),
                    {"fingerprint": fingerprint},
                ).scalar_one()

                duplicate_company = connection.execute(
                    text(
                        "SELECT 1 FROM appointments WHERE company_name_fingerprint=:fingerprint "
                        "AND status='active' AND dedupe_exception_id IS NULL LIMIT 1"
                    ),
                    {"fingerprint": fingerprint},
                ).scalar_one_or_none()
                exception_id: UUID | None = None
                if duplicate_company:
                    exception_id = connection.execute(
                        text(
                            "SELECT id FROM company_booking_exceptions "
                            "WHERE interviewer_user_id=:user_id "
                            "AND company_fingerprint=:fingerprint "
                            "AND consumed_at IS NULL AND revoked_at IS NULL AND expires_at>:now "
                            "ORDER BY id FOR UPDATE LIMIT 1"
                        ),
                        {"user_id": principal.id, "fingerprint": fingerprint, "now": now},
                    ).scalar_one_or_none()

                slots = [
                    SlotRow(**row)
                    for row in connection.execute(
                        text(
                            "SELECT id,start_at,end_at,status::text AS status "
                            "FROM appointment_slots WHERE id=ANY(CAST(:slot_ids AS uuid[])) "
                            "ORDER BY start_at ASC,id ASC FOR UPDATE"
                        ),
                        {"slot_ids": draft.slot_ids},
                    ).mappings()
                ]
                self._validate_slots(slots)
                start_at = slots[0].start_at
                end_at = start_at + timedelta(minutes=90)
                encrypted = self._encrypted_appointment_fields(appointment_id, draft)
                connection.execute(
                    text(
                        "INSERT INTO appointments "
                        "(id,user_id,company_id,dedupe_exception_id,start_at,end_at,status,"
                        "company_name_ciphertext,company_name_fingerprint,meeting_platform_ciphertext,"
                        "meeting_number_ciphertext,contact_ciphertext,notes_ciphertext,"
                        "version,created_at) "
                        "VALUES (:id,:user_id,:company_id,:exception_id,:start_at,:end_at,'active',"
                        ":company_name,:fingerprint,:platform,:number,:contact,:notes,1,:created_at)"
                    ),
                    {
                        "id": appointment_id,
                        "user_id": principal.id,
                        "company_id": company_id,
                        "exception_id": exception_id,
                        "start_at": start_at,
                        "end_at": end_at,
                        "fingerprint": fingerprint,
                        "created_at": now,
                        **encrypted,
                    },
                )
                if exception_id is not None:
                    connection.execute(
                        text("UPDATE company_booking_exceptions SET consumed_at=:now WHERE id=:id"),
                        {"now": now, "id": exception_id},
                    )
                updated = connection.execute(
                    text(
                        "UPDATE appointment_slots SET status='booked',"
                        "appointment_id=:appointment_id,"
                        "version=version+1 WHERE id=ANY(CAST(:slot_ids AS uuid[]))"
                    ),
                    {"appointment_id": appointment_id, "slot_ids": draft.slot_ids},
                )
                if updated.rowcount != 3:
                    raise RuntimeError("locked slot update did not affect exactly three rows")
                self._write_events_and_audit(
                    connection, appointment_id, principal.id, start_at, now
                )
        except IntegrityError as error:
            self._raise_integrity_error(error)

        return Appointment(
            **draft.model_dump(),
            id=appointment_id,
            status="active",
            version=1,
            start_at=start_at,
            end_at=end_at,
        )

    @staticmethod
    def _validate_slots(slots: list[SlotRow]) -> None:
        if len(slots) != 3 or any(slot.status != "available" for slot in slots):
            if any(slot.status == "owner_locked" for slot in slots):
                raise AuthError("OWNER_LOCKED", 409, "Owner locked", "Selected slots are locked")
            raise AuthError("SLOT_TAKEN", 409, "Slot taken", "Selected slots are unavailable")
        if any(slot.end_at - slot.start_at != timedelta(minutes=30) for slot in slots):
            raise AuthError("SLOT_TAKEN", 409, "Slot taken", "Selected slots are invalid")
        local_dates = {slot.start_at.astimezone(LOCAL_TIME).date() for slot in slots}
        if (
            len(local_dates) != 1
            or slots[1].start_at != slots[0].end_at
            or slots[2].start_at != slots[1].end_at
        ):
            raise AuthError("SLOT_TAKEN", 409, "Slot taken", "Selected slots are not consecutive")

    def _encrypted_appointment_fields(
        self, appointment_id: UUID, draft: AppointmentDraft
    ) -> dict[str, bytes | None]:
        contact = json.dumps(
            {
                "last_name": draft.contact_last_name,
                "salutation": draft.contact_salutation,
                "phone": draft.contact_phone,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        values = {
            "company_name": draft.company_name,
            "platform": draft.meeting_platform,
            "number": draft.meeting_number,
            "contact": contact,
        }
        columns = {
            "company_name": "company_name_ciphertext",
            "platform": "meeting_platform_ciphertext",
            "number": "meeting_number_ciphertext",
            "contact": "contact_ciphertext",
        }
        result: dict[str, bytes | None] = {
            name: self._cipher.encrypt(value, "appointments", columns[name], appointment_id)
            for name, value in values.items()
        }
        result["notes"] = (
            self._cipher.encrypt(draft.notes, "appointments", "notes_ciphertext", appointment_id)
            if draft.notes is not None
            else None
        )
        return result

    @staticmethod
    def _write_events_and_audit(
        connection: Any,
        appointment_id: UUID,
        user_id: UUID,
        start_at: datetime,
        now: datetime,
    ) -> None:
        for event_type, scheduled_at in (
            ("appointment_created", None),
            ("reminder_due", start_at - timedelta(minutes=10)),
        ):
            connection.execute(
                text(
                    "INSERT INTO notification_events "
                    "(id,type,biz_id,scheduled_at,idempotency_key,status,created_at) "
                    "VALUES (:id,:type,:biz_id,:scheduled_at,:key,'pending',:created_at)"
                ),
                {
                    "id": uuid4(),
                    "type": event_type,
                    "biz_id": appointment_id,
                    "scheduled_at": scheduled_at,
                    "key": f"appointment:{appointment_id}:{event_type}",
                    "created_at": now,
                },
            )
        connection.execute(
            text(
                "INSERT INTO audit_logs (id,actor,action,target,masked_detail,created_at) "
                "VALUES (:id,:actor,'appointment.created',:target,:detail,:created_at)"
            ),
            {
                "id": uuid4(),
                "actor": str(user_id),
                "target": str(appointment_id),
                "detail": "categories=company,meeting,contact,notes",
                "created_at": now,
            },
        )

    @staticmethod
    def _raise_integrity_error(error: IntegrityError) -> None:
        diagnostic = getattr(error.orig, "diag", None)
        constraint = getattr(diagnostic, "constraint_name", None)
        mapping = {
            "uq_active_user": ("DUP_ACCOUNT", "Account already has an active appointment"),
            "uq_active_company": ("DUP_COMPANY", "Company already has an active appointment"),
            "uq_appointment_exception": ("DUP_COMPANY", "Company exception was already consumed"),
        }
        if constraint not in mapping:
            raise error
        code, detail = mapping[constraint]
        raise AuthError(code, 409, "Duplicate appointment", detail) from error

"""Seed a local-only interviewer and two weeks of appointment slots."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text

from app.auth.passwords import PasswordHasher

LOCAL_TIME = ZoneInfo("Asia/Shanghai")


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def _slot_status(day: date, at: time, today: date) -> str:
    if day <= today or day.weekday() >= 5 or time(12) <= at < time(14) or time(18) <= at < time(20):
        return "unavailable"
    return "available"


def main() -> None:
    database_url = _required("JIANLI_DATABASE_URL")
    email = _required("JIANLI_DEMO_EMAIL").strip().lower()
    password = _required("JIANLI_DEMO_PASSWORD")
    engine = create_engine(database_url)
    today = datetime.now(LOCAL_TIME).date()
    monday = today - timedelta(days=today.weekday())
    with engine.begin() as connection:
        user_id = connection.execute(
            text("SELECT id FROM users WHERE email=:email"), {"email": email}
        ).scalar_one_or_none()
        if user_id is None:
            user_id = uuid4()
            connection.execute(
                text(
                    "INSERT INTO users (id,email,password_hash,role,verified) "
                    "VALUES (:id,:email,:password_hash,'interviewer',true)"
                ),
                {
                    "id": user_id,
                    "email": email,
                    "password_hash": PasswordHasher().hash(password),
                },
            )
        for day_offset in range(14):
            day = monday + timedelta(days=day_offset)
            for slot_index in range(25):
                local_start = datetime.combine(day, time(9, 30), LOCAL_TIME) + timedelta(
                    minutes=30 * slot_index
                )
                start_at = local_start.astimezone(UTC)
                connection.execute(
                    text(
                        "INSERT INTO appointment_slots (id,start_at,end_at,status,version) "
                        "VALUES (:id,:start_at,:end_at,CAST(:status AS slot_status),1) "
                        "ON CONFLICT (start_at,end_at) DO UPDATE SET status=EXCLUDED.status "
                        "WHERE appointment_slots.appointment_id IS NULL"
                    ),
                    {
                        "id": uuid4(),
                        "start_at": start_at,
                        "end_at": start_at + timedelta(minutes=30),
                        "status": _slot_status(day, local_start.time(), today),
                    },
                )
    engine.dispose()
    print(f"Seeded local demo account {email} and two-week slot grid")


if __name__ == "__main__":
    main()

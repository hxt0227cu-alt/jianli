"""Slot materializer rule and real PostgreSQL idempotency tests."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine, text

from app.appointments.materialize_slots import (
    _base_available,
    _override_status,
    load_calendar,
    materialize_slots,
)

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
LOCAL_TIME = ZoneInfo("Asia/Shanghai")


def test_official_calendar_and_daily_rules() -> None:
    calendar = load_calendar(2026)
    today = date(2026, 9, 13)
    assert _base_available(date(2026, 9, 14), time(9, 30), today, calendar)
    assert not _base_available(date(2026, 9, 14), time(12), today, calendar)
    assert not _base_available(date(2026, 9, 19), time(9, 30), today, calendar)
    assert _base_available(date(2026, 9, 20), time(9, 30), today, calendar)
    assert not _base_available(date(2026, 9, 25), time(9, 30), today, calendar)
    assert not _base_available(today, time(9, 30), today, calendar)


def test_owner_override_wins_and_missing_year_fails_closed(tmp_path: Path) -> None:
    start = datetime(2026, 9, 20, 1, 30, tzinfo=UTC)
    covering = {"start_at": start, "end_at": start + timedelta(minutes=30)}
    assert _override_status(
        start,
        start + timedelta(minutes=30),
        [{**covering, "action": "force_available"}],
    ) == "available"
    assert _override_status(
        start,
        start + timedelta(minutes=30),
        [
            {**covering, "action": "force_available"},
            {**covering, "action": "force_unavailable"},
        ],
    ) == "unavailable"
    with pytest.raises(RuntimeError, match="official calendar is missing"):
        load_calendar(2027, tmp_path)


@pytest.mark.skipif(not DATABASE_URL, reason="real PostgreSQL is required")
def test_materializer_is_idempotent_and_preserves_terminal_slots() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL)
    monday = date(2026, 9, 14)
    window_start = datetime.combine(monday, time.min, LOCAL_TIME).astimezone(UTC)
    window_end = window_start + timedelta(weeks=3)
    booked_start = datetime.combine(monday, time(9, 30), LOCAL_TIME).astimezone(UTC)
    locked_start = booked_start + timedelta(minutes=30)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM appointment_slots WHERE start_at>=:start AND start_at<:end"
                ),
                {"start": window_start, "end": window_end},
            )
            for slot_start, status, version in (
                (booked_start, "booked", 7),
                (locked_start, "owner_locked", 9),
            ):
                connection.execute(
                    text(
                        "INSERT INTO appointment_slots "
                        "(id,start_at,end_at,status,appointment_id,version) "
                        "VALUES (:id,:start,:end,CAST(:status AS slot_status),NULL,:version)"
                    ),
                    {
                        "id": uuid4(),
                        "start": slot_start,
                        "end": slot_start + timedelta(minutes=30),
                        "status": status,
                        "version": version,
                    },
                )
        assert materialize_slots(
            engine, start_day=monday, weeks=3, today=date(2026, 9, 13)
        ) == 525
        with engine.connect() as connection:
            first = connection.execute(
                text(
                    "SELECT start_at,status::text AS status,version FROM appointment_slots "
                    "WHERE start_at>=:start AND start_at<:end ORDER BY start_at"
                ),
                {"start": window_start, "end": window_end},
            ).mappings().all()
        assert len(first) == 525
        assert (first[0]["status"], first[0]["version"]) == ("booked", 7)
        assert (first[1]["status"], first[1]["version"]) == ("owner_locked", 9)
        snapshot = [(row["start_at"], row["status"], row["version"]) for row in first]
        materialize_slots(engine, start_day=monday, weeks=3, today=date(2026, 9, 13))
        with engine.connect() as connection:
            second = connection.execute(
                text(
                    "SELECT start_at,status::text AS status,version FROM appointment_slots "
                    "WHERE start_at>=:start AND start_at<:end ORDER BY start_at"
                ),
                {"start": window_start, "end": window_end},
            ).mappings().all()
        assert snapshot == [
            (row["start_at"], row["status"], row["version"]) for row in second
        ]
        by_local = {
            row["start_at"].astimezone(LOCAL_TIME): row["status"] for row in second
        }
        assert by_local[datetime(2026, 9, 20, 9, 30, tzinfo=LOCAL_TIME)] == "available"
        assert by_local[datetime(2026, 9, 25, 9, 30, tzinfo=LOCAL_TIME)] == "unavailable"
        assert by_local[datetime(2026, 9, 21, 12, 0, tzinfo=LOCAL_TIME)] == "unavailable"
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM appointment_slots WHERE start_at>=:start AND start_at<:end"
                ),
                {"start": window_start, "end": window_end},
            )
        engine.dispose()

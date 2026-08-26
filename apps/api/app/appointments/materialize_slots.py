"""Idempotently materialize the rolling production appointment calendar."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import Engine, create_engine, text

from app.config import Settings

LOCAL_TIME = ZoneInfo("Asia/Shanghai")
CALENDAR_DIR = Path(__file__).with_name("calendars")
DAY_START = time(9, 30)
SLOT_COUNT = 25
MEALS = ((time(12), time(14)), (time(18), time(20)))


@dataclass(frozen=True)
class OfficialCalendar:
    year: int
    holidays: frozenset[date]
    adjusted_workdays: frozenset[date]


def load_calendar(year: int, calendar_dir: Path = CALENDAR_DIR) -> OfficialCalendar:
    path = calendar_dir / f"{year}.json"
    if not path.is_file():
        raise RuntimeError(f"official calendar is missing for {year}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("year") != year or not payload.get("source"):
        raise RuntimeError(f"invalid official calendar metadata: {path}")
    return OfficialCalendar(
        year=year,
        holidays=frozenset(date.fromisoformat(value) for value in payload["holidays"]),
        adjusted_workdays=frozenset(
            date.fromisoformat(value) for value in payload["adjusted_workdays"]
        ),
    )


def _base_available(day: date, slot_start: time, today: date, calendar: OfficialCalendar) -> bool:
    if day <= today:
        return False
    working_day = day in calendar.adjusted_workdays or (
        day.weekday() < 5 and day not in calendar.holidays
    )
    if not working_day:
        return False
    return not any(start <= slot_start < end for start, end in MEALS)


def _override_status(
    start_at: datetime, end_at: datetime, overrides: list[dict[str, Any]]
) -> str | None:
    actions = {
        row["action"]
        for row in overrides
        if row["start_at"] <= start_at and row["end_at"] >= end_at
    }
    if "force_unavailable" in actions:
        return "unavailable"
    if "force_available" in actions:
        return "available"
    return None


def materialize_slots(
    engine: Engine,
    *,
    start_day: date,
    weeks: int = 8,
    today: date | None = None,
    calendar_dir: Path = CALENDAR_DIR,
) -> int:
    if weeks < 1 or weeks > 53:
        raise ValueError("weeks must be between 1 and 53")
    local_today = today or datetime.now(UTC).astimezone(LOCAL_TIME).date()
    first_day = start_day - timedelta(days=start_day.weekday())
    end_day = first_day + timedelta(weeks=weeks)
    calendars = {
        year: load_calendar(year, calendar_dir)
        for year in range(first_day.year, (end_day - timedelta(days=1)).year + 1)
    }
    window_start = datetime.combine(first_day, time.min, LOCAL_TIME).astimezone(UTC)
    window_end = datetime.combine(end_day, time.min, LOCAL_TIME).astimezone(UTC)
    with engine.begin() as connection:
        overrides = [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT start_at,end_at,action::text AS action FROM availability_overrides "
                    "WHERE start_at < :window_end AND end_at > :window_start"
                ),
                {"window_start": window_start, "window_end": window_end},
            ).mappings()
        ]
        processed = 0
        for day_offset in range(weeks * 7):
            day = first_day + timedelta(days=day_offset)
            calendar = calendars[day.year]
            for slot_offset in range(SLOT_COUNT):
                local_start = datetime.combine(day, DAY_START, LOCAL_TIME) + timedelta(
                    minutes=30 * slot_offset
                )
                start_at = local_start.astimezone(UTC)
                end_at = start_at + timedelta(minutes=30)
                status = _override_status(start_at, end_at, overrides)
                if status is None:
                    status = (
                        "available"
                        if _base_available(day, local_start.time(), local_today, calendar)
                        else "unavailable"
                    )
                connection.execute(
                    text(
                        "INSERT INTO appointment_slots "
                        "(id,start_at,end_at,status,appointment_id,version) "
                        "VALUES (:id,:start_at,:end_at,CAST(:status AS slot_status),NULL,1) "
                        "ON CONFLICT (start_at,end_at) DO UPDATE SET "
                        "status=CASE WHEN appointment_slots.status IN ('booked','owner_locked') "
                        "THEN appointment_slots.status ELSE EXCLUDED.status END, "
                        "version=CASE WHEN appointment_slots.status IN ('booked','owner_locked') "
                        "OR appointment_slots.status=EXCLUDED.status "
                        "THEN appointment_slots.version "
                        "ELSE appointment_slots.version+1 END"
                    ),
                    {
                        "id": uuid4(),
                        "start_at": start_at,
                        "end_at": end_at,
                        "status": status,
                    },
                )
                processed += 1
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weeks", type=int, default=8)
    parser.add_argument("--start-date", type=date.fromisoformat)
    args = parser.parse_args()
    start_day = args.start_date or datetime.now(UTC).astimezone(LOCAL_TIME).date()
    settings = Settings.from_env()
    if settings.database_url is None:
        raise RuntimeError("JIANLI_DATABASE_URL is required")
    engine = create_engine(settings.database_url)
    try:
        count = materialize_slots(engine, start_day=start_day, weeks=args.weeks)
    finally:
        engine.dispose()
    print(f"[slots] materialized={count} start={start_day.isoformat()} weeks={args.weeks}")


if __name__ == "__main__":
    main()

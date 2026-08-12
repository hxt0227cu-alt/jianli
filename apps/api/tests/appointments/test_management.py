from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, text

from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

# 复用同域已验证夹具与种子助手（单一来源，便于接手）
from .test_booking import (  # noqa: F401
    real_stack,
    _seed_user,
    _seed_slots,
    _authorized_client,
    _draft,
)


async def _create_appointment(
    client, engine: Engine, start: datetime, company: str = "Example, Inc."
) -> tuple[UUID, list[UUID]]:
    slots = _seed_slots(engine, start)
    draft = _draft(slots, company)
    preview = await client.post("/appointment-confirmations", json=draft)
    assert preview.status_code == 200, preview.status_code
    response = await client.post(
        "/appointments",
        headers={"Idempotency-Key": str(uuid4())},
        json={"confirmation_token": preview.json()["confirmation_token"], "appointment": draft},
    )
    assert response.status_code == 201, response.status_code
    return UUID(response.json()["id"]), slots


@pytest.mark.asyncio
async def test_list_my_returns_only_own_active_appointments(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    other = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client, _authorized_client(
        app, engine, settings, other
    ) as other_client:
        own_id, _ = await _create_appointment(client, engine, datetime(2030, 6, 3, 3, 0, tzinfo=UTC))
        # 第二个不同用户的预约必须用不同公司名，否则会命中 uq_active_company
        # （一家公司同一时刻只能有一条 active 预约，见 domain-model §6.6 / 迁移 0002）
        await _create_appointment(other_client, engine, datetime(2030, 6, 4, 3, 0, tzinfo=UTC), company="Other Corp")
        response = await client.get("/appointments")
        assert response.status_code == 200
        items = response.json()["items"]
        assert {UUID(item["id"]) for item in items} == {own_id}
        assert items[0]["company_name"] == "Example, Inc."
        assert items[0]["meeting_number"] == "123-456-789"
        assert items[0]["contact_phone"] == "13800000000"
        # 取消后从活动列表移除（已取消预约无关联时段，不应进入列表）
        cancelled = await client.delete(
            f"/appointments/{own_id}", headers={"Idempotency-Key": str(uuid4())}
        )
        assert cancelled.status_code == 204
        after = await client.get("/appointments")
        assert after.status_code == 200
        assert after.json()["items"] == []


@pytest.mark.asyncio
async def test_update_meeting_number_reencrypts_and_bumps_version(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        appointment_id, _ = await _create_appointment(
            client, engine, datetime(2030, 6, 5, 3, 0, tzinfo=UTC)
        )
        response = await client.patch(
            f"/appointments/{appointment_id}",
            headers={"Idempotency-Key": str(uuid4())},
            json={"version": 1, "meeting_number": "999-888-777"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["meeting_number"] == "999-888-777"
    assert body["version"] == 2
    with engine.connect() as connection:
        ciphertext = connection.execute(
            text("SELECT meeting_number_ciphertext FROM appointments WHERE id=:id"),
            {"id": appointment_id},
        ).scalar_one()
    assert ciphertext != b"123-456-789"


@pytest.mark.asyncio
async def test_reschedule_atomically_swaps_slots(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        appointment_id, old_slots = await _create_appointment(
            client, engine, datetime(2030, 6, 6, 3, 0, tzinfo=UTC)
        )
        new_slots = _seed_slots(engine, datetime(2030, 7, 6, 3, 0, tzinfo=UTC))
        response = await client.patch(
            f"/appointments/{appointment_id}",
            headers={"Idempotency-Key": str(uuid4())},
            json={"version": 1, "new_slot_ids": [str(value) for value in new_slots]},
        )
    assert response.status_code == 200
    assert response.json()["version"] == 2
    with engine.connect() as connection:
        old_status = connection.execute(
            text(
                "SELECT status::text FROM appointment_slots "
                "WHERE id=ANY(CAST(:ids AS uuid[])) ORDER BY id"
            ),
            {"ids": old_slots},
        ).scalars().all()
        new_rows = connection.execute(
            text(
                "SELECT status::text,appointment_id FROM appointment_slots "
                "WHERE id=ANY(CAST(:ids AS uuid[])) ORDER BY id"
            ),
            {"ids": new_slots},
        ).mappings().all()
        start_at = connection.execute(
            text("SELECT start_at FROM appointments WHERE id=:id"), {"id": appointment_id}
        ).scalar_one()
    assert all(status == "available" for status in old_status)
    assert all(row["status"] == "booked" and row["appointment_id"] == appointment_id for row in new_rows)
    assert start_at == datetime(2030, 7, 6, 3, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_cancel_releases_slots_and_sets_cancelled(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        appointment_id, slots = await _create_appointment(
            client, engine, datetime(2030, 6, 7, 3, 0, tzinfo=UTC)
        )
        response = await client.delete(
            f"/appointments/{appointment_id}", headers={"Idempotency-Key": str(uuid4())}
        )
    assert response.status_code == 204
    with engine.connect() as connection:
        status = connection.execute(
            text(
                "SELECT status::text FROM appointment_slots "
                "WHERE id=ANY(CAST(:ids AS uuid[])) ORDER BY id"
            ),
            {"ids": slots},
        ).scalars().all()
        appointment = connection.execute(
            text("SELECT status::text,cancelled_at FROM appointments WHERE id=:id"),
            {"id": appointment_id},
        ).mappings().one()
        cancelled_events = connection.execute(
            text(
                "SELECT status::text FROM notification_events "
                "WHERE biz_id=:id AND type='appointment_cancelled'"
            ),
            {"id": appointment_id},
        ).scalars().all()
    assert all(slot == "available" for slot in status)
    assert appointment["status"] == "cancelled" and appointment["cancelled_at"] is not None
    assert cancelled_events == ["pending"]


@pytest.mark.asyncio
async def test_cancel_others_appointment_is_forbidden(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    intruder = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as owner_client, _authorized_client(
        app, engine, settings, intruder
    ) as intruder_client:
        appointment_id, _ = await _create_appointment(
            owner_client, engine, datetime(2030, 6, 8, 3, 0, tzinfo=UTC)
        )
        response = await intruder_client.delete(
            f"/appointments/{appointment_id}", headers={"Idempotency-Key": str(uuid4())}
        )
    assert response.status_code == 403
    assert response.json()["code"] == "PERM_DENIED"


@pytest.mark.asyncio
async def test_update_version_mismatch_conflict(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        appointment_id, _ = await _create_appointment(
            client, engine, datetime(2030, 6, 9, 3, 0, tzinfo=UTC)
        )
        response = await client.patch(
            f"/appointments/{appointment_id}",
            headers={"Idempotency-Key": str(uuid4())},
            json={"version": 99, "meeting_number": "changed"},
        )
    assert response.status_code == 409
    assert response.json()["code"] == "VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_reschedule_slot_taken_keeps_original(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    rival = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as owner_client, _authorized_client(
        app, engine, settings, rival
    ) as rival_client:
        appointment_id, _ = await _create_appointment(
            owner_client, engine, datetime(2030, 6, 10, 3, 0, tzinfo=UTC)
        )
        _, target = await _create_appointment(
            rival_client, engine, datetime(2030, 7, 10, 3, 0, tzinfo=UTC), company="Rival Co"
        )
        response = await owner_client.patch(
            f"/appointments/{appointment_id}",
            headers={"Idempotency-Key": str(uuid4())},
            json={"version": 1, "new_slot_ids": [str(value) for value in target]},
        )
    assert response.status_code == 409
    assert response.json()["code"] == "SLOT_TAKEN"
    with engine.connect() as connection:
        appointment = connection.execute(
            text("SELECT status::text,version FROM appointments WHERE id=:id"),
            {"id": appointment_id},
        ).mappings().one()
        target_status = connection.execute(
            text(
                "SELECT status::text FROM appointment_slots "
                "WHERE id=ANY(CAST(:ids AS uuid[])) ORDER BY id"
            ),
            {"ids": target},
        ).scalars().all()
    assert appointment["status"] == "active" and appointment["version"] == 1
    assert all(status == "booked" for status in target_status)


@pytest.mark.asyncio
async def test_cancel_is_idempotent_when_already_cancelled(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        appointment_id, _ = await _create_appointment(
            client, engine, datetime(2030, 6, 11, 3, 0, tzinfo=UTC)
        )
        first = await client.delete(
            f"/appointments/{appointment_id}", headers={"Idempotency-Key": str(uuid4())}
        )
        second = await client.delete(
            f"/appointments/{appointment_id}", headers={"Idempotency-Key": str(uuid4())}
        )
    assert first.status_code == 204
    assert second.status_code == 204


@pytest.mark.asyncio
async def test_reschedule_two_transactions_race_for_slots(real_stack) -> None:
    engine, redis_client, app, settings = real_stack
    redis_client.flushdb()
    users = [_seed_user(engine), _seed_user(engine)]
    async with _authorized_client(app, engine, settings, users[0]) as first_client, _authorized_client(
        app, engine, settings, users[1]
    ) as second_client:
        first_id, _ = await _create_appointment(
            first_client, engine, datetime(2031, 3, 2, 3, 0, tzinfo=UTC)
        )
        second_id, _ = await _create_appointment(
            second_client, engine, datetime(2031, 3, 3, 3, 0, tzinfo=UTC), company="Second Co"
        )
        new_slots = _seed_slots(engine, datetime(2031, 4, 1, 3, 0, tzinfo=UTC))
        results = await asyncio.gather(
            first_client.patch(
                f"/appointments/{first_id}",
                headers={"Idempotency-Key": str(uuid4())},
                json={"version": 1, "new_slot_ids": [str(value) for value in new_slots]},
            ),
            second_client.patch(
                f"/appointments/{second_id}",
                headers={"Idempotency-Key": str(uuid4())},
                json={"version": 1, "new_slot_ids": [str(value) for value in new_slots]},
            ),
        )
    codes = sorted(result.status_code for result in results)
    assert codes == [200, 409]
    loser = next(result for result in results if result.status_code == 409)
    assert loser.json()["code"] == "SLOT_TAKEN"
    with engine.connect() as connection:
        booked_new = connection.execute(
            text(
                "SELECT count(*) FROM appointment_slots "
                "WHERE id=ANY(CAST(:ids AS uuid[])) AND status='booked'"
            ),
            {"ids": new_slots},
        ).scalar_one()
    assert booked_new == 3

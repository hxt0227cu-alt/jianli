from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request

from app.auth.models import Principal
from app.auth.router import _principal, _require_csrf
from app.auth.runtime import AuthRuntime

from .models import (
    Appointment,
    AppointmentDraft,
    AppointmentPreview,
    AppointmentUpdate,
    CreateAppointmentRequest,
    SlotSnapshot,
)
from .service import BookingService


def create_appointment_router(
    auth_runtime: AuthRuntime, booking_service: BookingService
) -> APIRouter:
    router = APIRouter(tags=["Appointments"])

    def interviewer(request: Request) -> Principal:
        _require_csrf(request, auth_runtime)
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "interviewer")

    def viewer(request: Request) -> Principal:
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "interviewer")

    @router.get("/slots/snapshot", response_model=SlotSnapshot, operation_id="getSlotSnapshot")
    def snapshot(request: Request, week_offset: int = Query(default=0, ge=0, le=1)) -> SlotSnapshot:
        principal = auth_runtime.service.require_role(
            _principal(request, auth_runtime), "interviewer"
        )
        return booking_service.slot_snapshot(principal, week_offset)

    @router.get("/appointments", operation_id="listMyAppointments")
    def list_my(request: Request) -> dict[str, object]:
        return {"items": booking_service.list_my(viewer(request))}

    @router.post(
        "/appointment-confirmations",
        response_model=AppointmentPreview,
        operation_id="previewAppointment",
    )
    def preview(payload: AppointmentDraft, request: Request) -> AppointmentPreview:
        principal = interviewer(request)
        return booking_service.preview(principal, payload)

    @router.post(
        "/appointments",
        response_model=Appointment,
        status_code=201,
        operation_id="createAppointment",
    )
    def create(
        payload: CreateAppointmentRequest,
        request: Request,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
    ) -> Appointment:
        principal = interviewer(request)
        return booking_service.create(principal, payload.appointment, payload.confirmation_token)

    @router.patch(
        "/appointments/{appointment_id}",
        response_model=Appointment,
        operation_id="updateAppointment",
    )
    def update(
        appointment_id: UUID,
        payload: AppointmentUpdate,
        request: Request,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
    ) -> Appointment:
        principal = interviewer(request)
        return booking_service.update(principal, appointment_id, payload)

    @router.delete(
        "/appointments/{appointment_id}",
        status_code=204,
        operation_id="cancelAppointment",
    )
    def cancel(
        appointment_id: UUID,
        request: Request,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
    ) -> None:
        principal = interviewer(request)
        booking_service.cancel(principal, appointment_id)

    return router

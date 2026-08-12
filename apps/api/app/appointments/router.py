from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request

from app.auth.models import Principal
from app.auth.router import _principal, _require_csrf
from app.auth.runtime import AuthRuntime

from .models import Appointment, AppointmentDraft, AppointmentPreview, CreateAppointmentRequest
from .service import BookingService


def create_appointment_router(
    auth_runtime: AuthRuntime, booking_service: BookingService
) -> APIRouter:
    router = APIRouter(tags=["Appointments"])

    def interviewer(request: Request) -> Principal:
        _require_csrf(request, auth_runtime)
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "interviewer")

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

    return router

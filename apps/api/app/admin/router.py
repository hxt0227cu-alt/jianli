"""Admin operation routes: owner_admin RBAC + CSRF, mapping to the approved contract.

Security split follows ``docs/api/openapi.yaml``:
- Read endpoints (``GET``) require an owner_admin session cookie only; the contract
  declares ``cookieSession`` security and no ``CsrfToken`` parameter, so CSRF is not
  enforced on reads.
- State-changing endpoints require CSRF + same-origin (``_require_csrf``) and, where
  the contract lists it, an ``Idempotency-Key`` header.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import Response

from app.admin.models import (
    AvailabilityOverride,
    AvailabilityOverrideInput,
    CompanyBookingException,
    CompanyBookingExceptionInput,
)
from app.appointments.service import BookingService
from app.auth.models import Principal
from app.auth.router import _principal, _require_csrf
from app.auth.runtime import AuthRuntime


def create_admin_router(
    auth_runtime: AuthRuntime, booking_service: BookingService
) -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["Admin"])

    def admin_viewer(request: Request) -> Principal:
        # Reads: cookie session + owner_admin role, no CSRF (matches contract).
        return auth_runtime.service.require_role(
            _principal(request, auth_runtime), "owner_admin"
        )

    def admin_owner(request: Request) -> Principal:
        # Mutations: CSRF + same-origin + owner_admin role.
        _require_csrf(request, auth_runtime)
        return auth_runtime.service.require_role(
            _principal(request, auth_runtime), "owner_admin"
        )

    @router.get("/appointments", operation_id="adminListAppointments")
    def list_appointments(request: Request) -> dict[str, object]:
        admin_viewer(request)
        return {"items": booking_service.admin_list_appointments()}

    @router.post(
        "/appointments/{appointment_id}/force-cancel",
        status_code=204,
        operation_id="forceCancelAppointment",
    )
    def force_cancel(
        appointment_id: UUID,
        request: Request,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
        ],
    ) -> Response:
        actor = admin_owner(request)
        booking_service.force_cancel(actor, appointment_id)
        return Response(status_code=204)

    @router.get("/availability-overrides", operation_id="listAvailabilityOverrides")
    def list_overrides(request: Request) -> dict[str, object]:
        admin_viewer(request)
        return {
            "items": [AvailabilityOverride(**row) for row in booking_service.list_overrides()]
        }

    @router.post(
        "/availability-overrides",
        response_model=AvailabilityOverride,
        status_code=201,
        operation_id="createAvailabilityOverride",
    )
    def create_override(
        payload: AvailabilityOverrideInput, request: Request
    ) -> AvailabilityOverride:
        actor = admin_owner(request)
        return AvailabilityOverride(
            **booking_service.create_override(
                actor.id, payload.start_at, payload.end_at, payload.action, payload.reason
            )
        )

    @router.patch(
        "/availability-overrides/{override_id}",
        response_model=AvailabilityOverride,
        operation_id="updateAvailabilityOverride",
    )
    def update_override(
        override_id: UUID, payload: AvailabilityOverrideInput, request: Request
    ) -> AvailabilityOverride:
        actor = admin_owner(request)
        return AvailabilityOverride(
            **booking_service.update_override(
                actor.id,
                override_id,
                payload.start_at,
                payload.end_at,
                payload.action,
                payload.reason,
            )
        )

    @router.delete(
        "/availability-overrides/{override_id}",
        status_code=204,
        operation_id="deleteAvailabilityOverride",
    )
    def delete_override(override_id: UUID, request: Request) -> Response:
        actor = admin_owner(request)
        booking_service.delete_override(actor.id, override_id)
        return Response(status_code=204)

    @router.post(
        "/company-booking-exceptions",
        response_model=CompanyBookingException,
        status_code=201,
        operation_id="createCompanyBookingException",
    )
    def create_exception(
        payload: CompanyBookingExceptionInput, request: Request
    ) -> CompanyBookingException:
        # Contract ``createCompanyBookingException`` declares only ``CsrfToken``
        # (no ``Idempotency-Key``), so no idempotency header is required here.
        actor = admin_owner(request)
        return CompanyBookingException(
            **booking_service.create_company_exception(
                actor.id,
                payload.interviewer_user_id,
                payload.company_name,
                payload.reason,
                payload.expires_at,
            )
        )

    return router

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
from sqlalchemy import Engine, text

from app.admin.models import (
    AvailabilityOverride,
    AvailabilityOverrideInput,
    CompanyBookingException,
    CompanyBookingExceptionInput,
    OwnerContactConfigInput,
    OwnerContactConfigView,
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

    @router.put(
        "/owner-contact-config",
        response_model=OwnerContactConfigView,
        operation_id="updateOwnerContactConfig",
    )
    def update_owner_contact(
        payload: OwnerContactConfigInput, request: Request
    ) -> OwnerContactConfigView:
        # Contract ``updateOwnerContactConfig`` declares only ``CsrfToken``.
        # CSRF + owner_admin RBAC are enforced by admin_owner (the actor identity is
        # resolved from the unique active owner_admin, not from the session actor).
        admin_owner(request)
        booking_service.update_owner_contact_config(payload.candidate_feishu_open_id)
        return OwnerContactConfigView(configured=True)

    # ----- Admin operations cockpit (2026-08-16): all-interviewers QA dashboard -----

    def _engine(request: Request) -> Engine:
        return request.app.state.engine

    @router.get("/conversations", operation_id="adminListConversations")
    def list_conversations(request: Request) -> dict[str, object]:
        admin_viewer(request)
        engine = _engine(request)
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT c.id, c.user_id, u.email, c.created_at, c.updated_at, "
                    "(SELECT COUNT(*) FROM conversation_messages WHERE conversation_id = c.id) AS message_count "  # noqa: E501
                    "FROM conversations c JOIN users u ON u.id = c.user_id "
                    "ORDER BY c.updated_at DESC LIMIT 100"
                )
            ).mappings().all()
        return {
            "items": [
                {
                    "id": str(row["id"]),
                    "user_id": str(row["user_id"]),
                    "user_email": row["email"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                    "message_count": int(row["message_count"]),
                }
                for row in rows
            ]
        }

    @router.get("/conversations/{conversation_id}/messages", operation_id="adminListConversationMessages")  # noqa: E501
    def list_conversation_messages(conversation_id: UUID, request: Request) -> dict[str, object]:
        admin_viewer(request)
        engine = _engine(request)
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, role, content, is_offtopic, created_at "
                    "FROM conversation_messages WHERE conversation_id = :cid ORDER BY created_at"
                ),
                {"cid": conversation_id},
            ).mappings().all()
        return {
            "items": [
                {
                    "id": str(row["id"]),
                    "role": row["role"],
                    "content": row["content"],
                    "is_offtopic": bool(row["is_offtopic"]),
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]
        }

    @router.get("/aiqa-stats", operation_id="getAIQAStats")
    def aiqa_stats(request: Request) -> dict[str, object]:
        admin_viewer(request)
        engine = _engine(request)
        with engine.connect() as connection:
            totals = connection.execute(
                text(
                    "SELECT "
                    "(SELECT COUNT(*) FROM conversations) AS total_conversations, "
                    "(SELECT COUNT(*) FROM conversation_messages) AS total_messages, "
                    "(SELECT COUNT(*) FROM conversation_messages WHERE role = 'user') AS user_messages, "  # noqa: E501
                    "(SELECT COUNT(*) FROM conversation_messages WHERE role = 'assistant') AS assistant_messages, "  # noqa: E501
                    "(SELECT COUNT(*) FROM conversation_messages WHERE role = 'assistant' AND is_offtopic = true) AS offtopic_messages, "  # noqa: E501
                    "(SELECT COUNT(DISTINCT user_id) FROM conversations) AS active_users"
                )
            ).mappings().one()
            by_user = connection.execute(
                text(
                    "SELECT u.email, COUNT(c.id) AS conv_count "
                    "FROM conversations c JOIN users u ON u.id = c.user_id "
                    "GROUP BY u.email ORDER BY conv_count DESC LIMIT 10"
                )
            ).mappings().all()
            recent = connection.execute(
                text(
                    "SELECT date_trunc('day', created_at) AS day, COUNT(*) AS count "
                    "FROM conversation_messages "
                    "WHERE created_at > now() - interval '7 days' "
                    "GROUP BY day ORDER BY day"
                )
            ).mappings().all()
        assistant = int(totals["assistant_messages"])
        return {
            "totals": {
                "total_conversations": int(totals["total_conversations"]),
                "total_messages": int(totals["total_messages"]),
                "user_messages": int(totals["user_messages"]),
                "assistant_messages": assistant,
                "offtopic_messages": int(totals["offtopic_messages"]),
                "offtopic_rate": (int(totals["offtopic_messages"]) / assistant) if assistant else 0.0,  # noqa: E501
                "active_users": int(totals["active_users"]),
            },
            "by_user": [{"email": row["email"], "conversation_count": int(row["conv_count"])} for row in by_user],  # noqa: E501
            "recent_7d": [
                {"day": row["day"].date().isoformat(), "message_count": int(row["count"])} for row in recent  # noqa: E501
            ],
        }

    return router

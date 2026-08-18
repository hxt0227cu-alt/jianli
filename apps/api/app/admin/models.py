"""Admin operation request/response schemas, aligned to docs/api/openapi.yaml.

These are the API-layer contracts only. The business logic lives on
``BookingService`` (see ``app.appointments.service``); this package maps
request bodies in and response bodies out, and enforces RBAC + CSRF at the edge.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityOverrideInput(BaseModel):
    """Request body for create/update of an availability override."""

    model_config = ConfigDict(extra="forbid")

    start_at: datetime
    end_at: datetime
    action: Literal["force_unavailable", "force_available"]
    reason: str | None = Field(default=None, max_length=500)


class AvailabilityOverride(BaseModel):
    """Response body for an availability override (input fields plus server-assigned)."""

    id: UUID
    start_at: datetime
    end_at: datetime
    action: Literal["force_unavailable", "force_available"]
    reason: str | None
    created_at: datetime


class CompanyBookingExceptionInput(BaseModel):
    """Request body for creating a one-time duplicate-booking exception."""

    model_config = ConfigDict(extra="forbid")

    interviewer_user_id: UUID
    company_name: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=1000)
    expires_at: datetime


class CompanyBookingException(BaseModel):
    """Response body for a created company booking exception.

    The store keeps only the company HMAC fingerprint (never plaintext), so the
    human-readable ``company_name`` is echoed back from the request.
    """

    id: UUID
    interviewer_user_id: UUID
    company_name: str
    reason: str
    expires_at: datetime
    created_at: datetime


class OwnerContactConfigInput(BaseModel):
    """Request body for configuring the candidate Feishu open_id (R13, OpenAPI v0.3)."""

    model_config = ConfigDict(extra="forbid")

    candidate_feishu_open_id: str = Field(min_length=5, max_length=100)


class OwnerContactConfigView(BaseModel):
    """Response body confirming the candidate Feishu open_id was configured.

    The stored value is AES ciphertext (never echoed back in plaintext); the view
    only reports that the configuration exists.
    """

    configured: bool

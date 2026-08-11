from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppointmentDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_ids: list[UUID] = Field(min_length=3, max_length=3)
    company_name: str = Field(min_length=1, max_length=200)
    meeting_platform: str = Field(min_length=1, max_length=100)
    meeting_number: str = Field(min_length=1, max_length=200)
    contact_last_name: str = Field(min_length=1, max_length=50)
    contact_salutation: str = Field(min_length=1, max_length=20)
    contact_phone: str = Field(min_length=5, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "company_name",
        "meeting_platform",
        "meeting_number",
        "contact_last_name",
        "contact_salutation",
        "contact_phone",
    )
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("slot_ids")
    @classmethod
    def require_distinct_slots(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != 3:
            raise ValueError("slot ids must be distinct")
        return value


class AppointmentPreview(BaseModel):
    confirmation_token: str
    expires_at: datetime
    company_name: str
    recipient_email: str
    salutation: str


class CreateAppointmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_token: str
    appointment: AppointmentDraft


class Appointment(AppointmentDraft):
    id: UUID
    status: Literal["active", "cancelled", "completed"]
    version: int = Field(ge=1)
    start_at: datetime
    end_at: datetime

"""SQLAlchemy Core repository for the approved identity schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, text

from .models import Principal


class AuthRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT id,email,password_hash,role,verified FROM users "
                        "WHERE email=:email AND deleted_at IS NULL"
                    ),
                    {"email": email},
                )
                .mappings()
                .one_or_none()
            )
        return dict(row) if row else None

    def create_session(
        self,
        session_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        device: str | None,
        ip: str | None,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO auth_sessions "
                    "(id,user_id,session_token_hash,device,ip,expires_at,revoked_at) "
                    "VALUES (:id,:user_id,:token_hash,:device,CAST(:ip AS inet),:expires_at,NULL)"
                ),
                {
                    "id": session_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "device": device,
                    "ip": ip,
                    "expires_at": expires_at,
                },
            )

    def find_principal(self, token_hash: str, now: datetime) -> Principal | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT u.id,u.email,u.role,u.verified FROM auth_sessions s "
                        "JOIN users u ON u.id=s.user_id "
                        "WHERE s.session_token_hash=:token_hash AND s.revoked_at IS NULL "
                        "AND s.expires_at>:now AND u.deleted_at IS NULL"
                    ),
                    {"token_hash": token_hash, "now": now},
                )
                .mappings()
                .one_or_none()
            )
        return Principal(**row) if row else None

    def revoke_session(self, token_hash: str, now: datetime) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    "UPDATE auth_sessions SET revoked_at=:now "
                    "WHERE session_token_hash=:token_hash AND revoked_at IS NULL"
                ),
                {"token_hash": token_hash, "now": now},
            )
        return bool(result.rowcount)

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

    def find_email_by_user_id(self, user_id: UUID) -> str | None:
        with self._engine.connect() as connection:
            return connection.execute(
                text("SELECT email FROM users WHERE id=:user_id AND deleted_at IS NULL"),
                {"user_id": user_id},
            ).scalar()

    def create_session(
        self,
        session_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        device: str | None,
        ip: str | None,
        previous_token_hash: str | None = None,
    ) -> None:
        with self._engine.begin() as connection:
            if previous_token_hash:
                connection.execute(
                    text(
                        "UPDATE auth_sessions SET revoked_at=now() "
                        "WHERE session_token_hash=:token_hash AND revoked_at IS NULL"
                    ),
                    {"token_hash": previous_token_hash},
                )
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

    # --- Account self-service (M4): register / verify / reset -------------------

    def create_user(
        self,
        user_id: UUID,
        email: str,
        password_hash: str,
        role: str,
        verified: bool,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id,email,password_hash,role,verified) "
                    "VALUES (:id,:email,:password_hash,:role,:verified)"
                ),
                {
                    "id": user_id,
                    "email": email,
                    "password_hash": password_hash,
                    "role": role,
                    "verified": verified,
                },
            )

    def create_verification_token(
        self, token_id: UUID, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO email_verification_tokens (id,user_id,token_hash,expires_at) "
                    "VALUES (:id,:user_id,:token_hash,:expires_at)"
                ),
                {
                    "id": token_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )

    def replace_verification_token(
        self,
        token_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        """Invalidate every old unused registration code and insert its replacement."""

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE email_verification_tokens SET consumed_at=:now "
                    "WHERE user_id=:user_id AND consumed_at IS NULL"
                ),
                {"user_id": user_id, "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO email_verification_tokens (id,user_id,token_hash,expires_at) "
                    "VALUES (:id,:user_id,:token_hash,:expires_at)"
                ),
                {
                    "id": token_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )

    def find_verification_token(
        self, token_hash: str, now: datetime
    ) -> dict[str, Any] | None:
        """Return an unused, unexpired verification token (id, user_id)."""

        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT id,user_id FROM email_verification_tokens "
                        "WHERE token_hash=:token_hash AND consumed_at IS NULL AND expires_at>:now"
                    ),
                    {"token_hash": token_hash, "now": now},
                )
                .mappings()
                .one_or_none()
            )
        return dict(row) if row else None

    def find_verification_token_user(self, token_hash: str) -> dict[str, Any] | None:
        """Idempotency probe: a not-yet-expired token (consumed allowed) with its
        user's verified flag."""

        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT t.id,t.user_id,t.consumed_at,u.verified "
                        "FROM email_verification_tokens t JOIN users u ON u.id=t.user_id "
                        "WHERE t.token_hash=:token_hash AND t.expires_at>now() "
                        "AND u.deleted_at IS NULL"
                    ),
                    {"token_hash": token_hash},
                )
                .mappings()
                .one_or_none()
            )
        return dict(row) if row else None

    def consume_verification_token(self, token_id: UUID, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE email_verification_tokens SET consumed_at=:now "
                    "WHERE id=:id AND consumed_at IS NULL"
                ),
                {"id": token_id, "now": now},
            )

    def mark_user_verified(self, user_id: UUID, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text("UPDATE users SET verified=true WHERE id=:user_id"),
                {"user_id": user_id},
            )

    def create_reset_token(
        self, token_id: UUID, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO password_reset_tokens (id,user_id,token_hash,expires_at) "
                    "VALUES (:id,:user_id,:token_hash,:expires_at)"
                ),
                {
                    "id": token_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )

    def find_reset_token(self, token_hash: str, now: datetime) -> dict[str, Any] | None:
        """Return an unused, unexpired reset token (id, user_id)."""

        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT id,user_id FROM password_reset_tokens "
                        "WHERE token_hash=:token_hash AND consumed_at IS NULL AND expires_at>:now"
                    ),
                    {"token_hash": token_hash, "now": now},
                )
                .mappings()
                .one_or_none()
            )
        return dict(row) if row else None

    def consume_reset_token(self, token_id: UUID, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE password_reset_tokens SET consumed_at=:now "
                    "WHERE id=:id AND consumed_at IS NULL"
                ),
                {"id": token_id, "now": now},
            )

    def update_password(self, user_id: UUID, password_hash: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE users SET password_hash=:password_hash "
                    "WHERE id=:user_id AND deleted_at IS NULL"
                ),
                {"user_id": user_id, "password_hash": password_hash},
            )

    def revoke_all_sessions(self, user_id: UUID, now: datetime) -> None:
        """Invalidate every active session for a user (used after password reset)."""

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE auth_sessions SET revoked_at=:now "
                    "WHERE user_id=:user_id AND revoked_at IS NULL"
                ),
                {"user_id": user_id, "now": now},
            )

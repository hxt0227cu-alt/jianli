"""Authentication use cases over approved storage and security primitives."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.notifications.email import (
    EmailSender,
    render_reset_email,
    render_verification_email,
    web_base_url,
)

from .errors import AuthError
from .models import Principal, UserRole, UserSummary
from .passwords import PasswordHasher, PasswordPolicyError
from .rate_limit import LoginRateLimiter
from .repository import AuthRepository
from .tokens import SessionTokens

SESSION_HOURS = 12
REMEMBER_DAYS = 14
VERIFICATION_TTL = timedelta(hours=24)
RESET_TTL = timedelta(hours=1)
DEFAULT_ROLE: UserRole = "interviewer"
SECURITY_LOGGER = logging.getLogger("jianli.security.auth")


def _log_account_failure(
    account_tag: str, ip: str, result: str, request_id: str | None = None
) -> None:
    ip_prefix = ip.rsplit(".", 1)[0] if "." in ip else ip[:19]
    SECURITY_LOGGER.warning(
        json.dumps(
            {
                "event": "auth_account_failure",
                "account_id": account_tag,
                "request_id": request_id or str(uuid4()),
                "result": result,
                "ip_prefix": ip_prefix,
            },
            separators=(",", ":"),
        )
    )


@dataclass(frozen=True, slots=True)
class SessionGrant:
    token: str
    csrf_token: str
    max_age_seconds: int


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        passwords: PasswordHasher,
        tokens: SessionTokens,
        rate_limiter: LoginRateLimiter,
        email_sender: EmailSender | None = None,
    ) -> None:
        self._repository = repository
        self._passwords = passwords
        self._tokens = tokens
        self._rate_limiter = rate_limiter
        self._email_sender = email_sender

    def login(
        self,
        email: str,
        password: str,
        remember_me: bool,
        ip: str,
        device: str | None,
        current_token: str | None = None,
        request_id: str | None = None,
    ) -> SessionGrant:
        account_tag = self._rate_limiter.account_tag(email)
        try:
            self._rate_limiter.check_ip(ip)
            self._rate_limiter.check_account(email)
        except AuthError as error:
            _log_account_failure(account_tag, ip, error.code, request_id)
            raise
        user = self._repository.find_user_by_email(email)
        password_hash = str(user["password_hash"]) if user else None
        if not self._passwords.verify(password, password_hash):
            try:
                self._rate_limiter.record_failure(email)
            except AuthError:
                _log_account_failure(account_tag, ip, "RATE_LIMITED", request_id)
                raise
            _log_account_failure(account_tag, ip, "INVALID_CREDENTIALS", request_id)
            raise AuthError(
                "INVALID_CREDENTIALS", 401, "Invalid credentials", "Invalid credentials"
            )
        assert user is not None
        if not bool(user["verified"]):
            _log_account_failure(account_tag, ip, "EMAIL_UNVERIFIED", request_id)
            raise AuthError("EMAIL_UNVERIFIED", 403, "Email unverified", "Verify email first")

        self._rate_limiter.clear_failures(email)
        now = datetime.now(UTC)
        lifetime = timedelta(days=REMEMBER_DAYS) if remember_me else timedelta(hours=SESSION_HOURS)
        token = self._tokens.generate()
        self._repository.create_session(
            uuid4(),
            user["id"],
            self._tokens.digest(token),
            now + lifetime,
            device,
            ip,
            self._tokens.digest(current_token) if current_token else None,
        )
        return SessionGrant(token, self._tokens.csrf(token), int(lifetime.total_seconds()))

    def authenticate(self, token: str | None) -> Principal:
        if not token:
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
        principal = self._repository.find_principal(self._tokens.digest(token), datetime.now(UTC))
        if principal is None:
            raise AuthError("AUTH_EXPIRED", 401, "Session expired", "Login again")
        return principal

    def logout(self, token: str) -> None:
        if not self._repository.revoke_session(self._tokens.digest(token), datetime.now(UTC)):
            raise AuthError("AUTH_EXPIRED", 401, "Session expired", "Login again")

    def require_role(self, principal: Principal, *allowed: UserRole) -> Principal:
        if principal.role not in allowed:
            _log_account_failure(
                self._rate_limiter.account_tag(principal.email), "unknown", "PERM_DENIED"
            )
            raise AuthError(
                "PERM_DENIED",
                403,
                "Permission denied",
                "Permission denied",
            )
        return principal

    # --- Account self-service (M4): register / verify / reset -------------------

    def register(self, email: str, password: str, ip: str) -> UserSummary:
        """Create an unverified interviewer and issue a verification token.

        Security invariants: password is BCrypt-hashed (policy enforced by
        ``PasswordHasher``); the verification token is stored only as its SHA-256
        hash; email delivery is best-effort (skipped when no SMTP is configured).
        """

        self._rate_limiter.check_ip(ip)
        if self._repository.find_user_by_email(email) is not None:
            raise AuthError(
                "DUPLICATE_EMAIL",
                409,
                "Email already registered",
                "Use login or reset your password",
            )
        try:
            password_hash = self._passwords.hash(password)
        except PasswordPolicyError as err:
            raise AuthError(
                "INVALID_REQUEST",
                422,
                "Weak password",
                "Password must be 10-72 UTF-8 bytes",
            ) from err
        user_id = uuid4()
        self._repository.create_user(
            user_id, email, password_hash, DEFAULT_ROLE, False
        )
        token = self._tokens.generate()
        self._repository.create_verification_token(
            uuid4(), user_id, self._tokens.digest(token), datetime.now(UTC) + VERIFICATION_TTL
        )
        self._send_verification_email(email, token)
        return UserSummary(id=user_id, email=email, role=DEFAULT_ROLE, verified=False)

    def verify_email(self, token: str) -> None:
        """Consume a verification token and mark the account verified.

        Idempotent: a second call for an already-verified account succeeds (204).
        """

        token_hash = self._tokens.digest(token)
        valid = self._repository.find_verification_token(token_hash, datetime.now(UTC))
        if valid is not None:
            self._repository.consume_verification_token(valid["id"], datetime.now(UTC))
            self._repository.mark_user_verified(valid["user_id"], datetime.now(UTC))
            return
        existing = self._repository.find_verification_token_user(token_hash)
        if existing is not None and existing["verified"]:
            return  # already verified via this (or another) link
        raise AuthError(
            "INVALID_TOKEN",
            409,
            "Invalid or expired token",
            "Request a new verification email",
        )

    def request_password_reset(self, email: str, ip: str) -> None:
        """Create a reset token and email it. Always returns (202); never reveals
        whether the email exists (anti-enumeration)."""

        self._rate_limiter.check_ip(ip)
        user = self._repository.find_user_by_email(email)
        if user is None:
            return
        token = self._tokens.generate()
        self._repository.create_reset_token(
            uuid4(),
            user["id"],
            self._tokens.digest(token),
            datetime.now(UTC) + RESET_TTL,
        )
        self._send_reset_email(email, token)

    def reset_password(self, token: str, new_password: str) -> None:
        """Consume a reset token, set a new BCrypt password, and revoke all sessions.

        Revoking every session on reset prevents a stolen/old session from surviving
        a password change.
        """

        try:
            password_hash = self._passwords.hash(new_password)
        except PasswordPolicyError as err:
            raise AuthError(
                "INVALID_REQUEST",
                422,
                "Weak password",
                "Password must be 10-72 UTF-8 bytes",
            ) from err
        token_hash = self._tokens.digest(token)
        row = self._repository.find_reset_token(token_hash, datetime.now(UTC))
        if row is None:
            raise AuthError(
                "INVALID_TOKEN",
                409,
                "Invalid or expired token",
                "Request a new reset link",
            )
        self._repository.update_password(row["user_id"], password_hash)
        self._repository.consume_reset_token(row["id"], datetime.now(UTC))
        self._repository.revoke_all_sessions(row["user_id"], datetime.now(UTC))

    def _send_verification_email(self, email: str, token: str) -> None:
        if self._email_sender is None:
            return
        link = f"{web_base_url()}/verify-email?token={token}"
        subject, body = render_verification_email(email, link)
        self._email_sender.send(email, subject, body)

    def _send_reset_email(self, email: str, token: str) -> None:
        if self._email_sender is None:
            return
        subject, body = render_reset_email(email, f"{web_base_url()}/reset-password?token={token}")
        self._email_sender.send(email, subject, body)

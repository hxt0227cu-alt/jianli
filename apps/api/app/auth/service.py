"""Authentication use cases over approved storage and security primitives."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.notifications.email import (
    EmailSender,
    render_reset_email,
    render_verification_email,
)

from .errors import AuthError
from .models import Principal, UserRole, UserSummary
from .passwords import PasswordHasher, PasswordPolicyError
from .rate_limit import LoginRateLimiter
from .repository import AuthRepository
from .tokens import SessionTokens

SESSION_HOURS = 12
REMEMBER_DAYS = 14
VERIFICATION_TTL = timedelta(minutes=10)  # PRD §5: verification code valid 10 min
RESET_TTL = timedelta(minutes=10)         # PRD §5: same 10-min window for reset codes
DEFAULT_ROLE: UserRole = "interviewer"
SECURITY_LOGGER = logging.getLogger("jianli.security.auth")
EMAIL_LOGGER = logging.getLogger("jianli.auth.email")
EmailCodeSink = Callable[[str, str, str], None]


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
        email_code_sink: EmailCodeSink | None = None,
    ) -> None:
        self._repository = repository
        self._passwords = passwords
        self._tokens = tokens
        self._rate_limiter = rate_limiter
        self._email_sender = email_sender
        self._email_code_sink = email_code_sink

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
        """Create an unverified interviewer and email a 6-digit verification code.

        Security invariants: password is BCrypt-hashed (policy enforced by
        ``PasswordHasher``); the code is stored only as its SHA-256 hash; code
        issuance is rate-limited (PRD §5: 60s/1, ≤3 per hour per email); email
        delivery is best-effort (skipped when no SMTP is configured).
        """

        self._rate_limiter.check_ip(ip)
        if self._repository.find_user_by_email(email) is not None:
            raise AuthError(
                "DUPLICATE_EMAIL",
                409,
                "Email already registered",
                "Use login or reset your password",
            )
        self._rate_limiter.check_verify_code_send(email, ip, "verify")
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
        code = self._tokens.generate_code()
        self._repository.create_verification_token(
            uuid4(), user_id, self._tokens.digest(code), datetime.now(UTC) + VERIFICATION_TTL
        )
        self._send_verification_email(email, code)
        return UserSummary(id=user_id, email=email, role=DEFAULT_ROLE, verified=False)

    def verify_email(self, code: str, ip: str) -> None:
        """Consume a 6-digit verification code and mark the account verified.

        Idempotent: a second call for an already-verified account succeeds (204).
        Brute force on the 6-digit code is throttled per IP (≤10 / min).
        """

        self._rate_limiter.check_verify_ip(ip)
        code_hash = self._tokens.digest(code)
        valid = self._repository.find_verification_token(code_hash, datetime.now(UTC))
        if valid is not None:
            self._repository.consume_verification_token(valid["id"], datetime.now(UTC))
            self._repository.mark_user_verified(valid["user_id"], datetime.now(UTC))
            return
        existing = self._repository.find_verification_token_user(code_hash)
        if existing is not None and existing["verified"]:
            return  # already verified via this (or another) code
        raise AuthError(
            "INVALID_VERIFY_CODE",
            422,
            "Invalid or expired verification code",
            "Check the 6-digit code in your email or request a new one",
        )

    def resend_email_verification(self, email: str, ip: str) -> None:
        """Replace an unverified account's code without revealing account state."""

        self._rate_limiter.check_ip(ip)
        self._rate_limiter.check_verify_code_send(email, ip, "verify")
        user = self._repository.find_user_by_email(email)
        if user is None or user["verified"]:
            return
        now = datetime.now(UTC)
        code = self._tokens.generate_code()
        self._repository.replace_verification_token(
            uuid4(),
            user["id"],
            self._tokens.digest(code),
            now + VERIFICATION_TTL,
            now,
        )
        self._send_verification_email(email, code)

    def request_password_reset(self, email: str, ip: str) -> None:
        """Create a reset code and email it. Always returns (202); never reveals
        whether the email exists (anti-enumeration)."""

        self._rate_limiter.check_ip(ip)
        self._rate_limiter.check_verify_code_send(email, ip, "reset")
        user = self._repository.find_user_by_email(email)
        if user is None:
            return
        code = self._tokens.generate_code()
        self._repository.create_reset_token(
            uuid4(),
            user["id"],
            self._tokens.digest(code),
            datetime.now(UTC) + RESET_TTL,
        )
        self._send_reset_email(email, code)

    def reset_password(self, code: str, new_password: str, ip: str) -> None:
        """Consume a 6-digit reset code, set a new BCrypt password, and revoke all sessions.

        Revoking every session on reset prevents a stolen/old session from surviving
        a password change. Brute force on the code is throttled per IP.
        """

        self._rate_limiter.check_verify_ip(ip)
        try:
            password_hash = self._passwords.hash(new_password)
        except PasswordPolicyError as err:
            raise AuthError(
                "INVALID_REQUEST",
                422,
                "Weak password",
                "Password must be 10-72 UTF-8 bytes",
            ) from err
        code_hash = self._tokens.digest(code)
        row = self._repository.find_reset_token(code_hash, datetime.now(UTC))
        if row is None:
            raise AuthError(
                "INVALID_VERIFY_CODE",
                422,
                "Invalid or expired reset code",
                "Check the 6-digit code in your email or request a new one",
            )
        self._repository.update_password(row["user_id"], password_hash)
        self._repository.consume_reset_token(row["id"], datetime.now(UTC))
        self._repository.revoke_all_sessions(row["user_id"], datetime.now(UTC))

    def _send_verification_email(self, email: str, code: str) -> None:
        subject, body = render_verification_email(email, code)
        self._deliver_email_code(email, code, "verification", subject, body)

    def _send_reset_email(self, email: str, code: str) -> None:
        subject, body = render_reset_email(email, code)
        self._deliver_email_code(email, code, "reset", subject, body)

    def _deliver_email_code(
        self,
        recipient: str,
        code: str,
        kind: str,
        subject: str,
        body: str,
    ) -> None:
        if self._email_sender is not None:
            try:
                self._email_sender.send(recipient, subject, body)
            except Exception as error:
                # Do not log the exception text: SMTP errors may echo recipients,
                # message bodies, credentials, or provider responses.
                EMAIL_LOGGER.warning(
                    "auth_email_delivery_failed kind=%s error_type=%s",
                    kind,
                    type(error).__name__,
                )
            return
        if self._email_code_sink is not None:
            self._email_code_sink(kind, recipient, code)

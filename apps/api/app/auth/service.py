"""Authentication use cases over approved storage and security primitives."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .errors import AuthError
from .models import Principal, UserRole
from .passwords import PasswordHasher
from .rate_limit import LoginRateLimiter
from .repository import AuthRepository
from .tokens import SessionTokens

SESSION_HOURS = 12
REMEMBER_DAYS = 14
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
    ) -> None:
        self._repository = repository
        self._passwords = passwords
        self._tokens = tokens
        self._rate_limiter = rate_limiter

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
            raise AuthError("AUTH_EXPIRED", 401, "Invalid credentials", "Invalid credentials")
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

"""Authentication use cases over approved storage and security primitives."""

from __future__ import annotations

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
    ) -> SessionGrant:
        self._rate_limiter.check_ip(ip)
        self._rate_limiter.check_account(email)
        user = self._repository.find_user_by_email(email)
        password_hash = str(user["password_hash"]) if user else None
        if not self._passwords.verify(password, password_hash):
            self._rate_limiter.record_failure(email)
            raise AuthError("AUTH_EXPIRED", 401, "Invalid credentials", "Invalid credentials")
        assert user is not None
        if not bool(user["verified"]):
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

    @staticmethod
    def require_role(principal: Principal, *allowed: UserRole) -> Principal:
        if principal.role not in allowed:
            raise AuthError("PERM_DENIED", 403, "Permission denied", "Permission denied")
        return principal

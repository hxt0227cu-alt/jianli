from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url

from app.auth.errors import AuthError
from app.auth.models import Principal
from app.auth.passwords import BCRYPT_COST, PasswordHasher, PasswordPolicyError
from app.auth.rate_limit import LoginRateLimiter
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import AuthRuntime, build_auth_runtime
from app.auth.service import AuthService
from app.auth.tokens import SessionTokens
from app.config import Settings
from app.factory import create_app

CSRF_KEY = "csrf-key-for-auth-tests-32-bytes!!"
RATE_KEY = "rate-key-for-auth-tests-32-bytes!!"
ORIGIN = "https://test.example"


class MemoryRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.values: dict[str, int] = {}
        self.keys_seen: list[str] = []

    def eval(self, _script: str, _numkeys: int, key: str, *args: int) -> list[int]:
        if self.fail:
            raise ConnectionError("injected Redis outage")
        window = args[0] if args else 900
        self.keys_seen.append(key)
        if "redis.call('GET'" in _script:
            return [self.values.get(key, 0), window]
        self.values[key] = self.values.get(key, 0) + 1
        return [self.values[key], window]

    def delete(self, *names: str) -> int:
        if self.fail:
            raise ConnectionError("injected Redis outage")
        return sum(self.values.pop(name, None) is not None for name in names)

    def close(self) -> None:
        return None


class MemoryRepository:
    def __init__(self, user: dict[str, Any] | None = None) -> None:
        self.user = user
        self.sessions: dict[str, tuple[Principal, datetime, bool]] = {}
        self.created_lifetimes: list[float] = []

    def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self.user if self.user and self.user["email"] == email else None

    def create_session(
        self,
        _session_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        _device: str | None,
        _ip: str | None,
        previous_token_hash: str | None = None,
    ) -> None:
        assert self.user and self.user["id"] == user_id
        principal = Principal(
            id=user_id,
            email=self.user["email"],
            role=self.user["role"],
            verified=self.user["verified"],
        )
        self.sessions[token_hash] = (principal, expires_at, False)
        if previous_token_hash in self.sessions:
            previous = self.sessions[previous_token_hash]
            self.sessions[previous_token_hash] = (previous[0], previous[1], True)
        self.created_lifetimes.append((expires_at - datetime.now(UTC)).total_seconds())

    def find_principal(self, token_hash: str, now: datetime) -> Principal | None:
        value = self.sessions.get(token_hash)
        if not value or value[2] or value[1] <= now:
            return None
        return value[0]

    def revoke_session(self, token_hash: str, _now: datetime) -> bool:
        value = self.sessions.get(token_hash)
        if not value or value[2]:
            return False
        self.sessions[token_hash] = (value[0], value[1], True)
        return True


@pytest.fixture(scope="session")
def passwords() -> PasswordHasher:
    return PasswordHasher()


def build_memory_runtime(
    passwords: PasswordHasher,
    *,
    verified: bool = True,
    role: str = "interviewer",
    redis_client: MemoryRedis | None = None,
) -> tuple[AuthRuntime, MemoryRepository, MemoryRedis]:
    user_id = uuid4()
    repository = MemoryRepository(
        {
            "id": user_id,
            "email": "person@example.invalid",
            "password_hash": passwords.hash("correct-password"),
            "role": role,
            "verified": verified,
        }
    )
    client = redis_client or MemoryRedis()
    tokens = SessionTokens(CSRF_KEY)
    service = AuthService(
        cast(Any, repository),
        passwords,
        tokens,
        LoginRateLimiter(client, RATE_KEY),
    )
    runtime = AuthRuntime(
        service,
        tokens,
        frozenset({ORIGIN}),
        cast(Engine, None),
        client,
    )
    return runtime, repository, client


def test_password_policy_uses_bcrypt_cost_and_utf8_byte_limits(passwords: PasswordHasher) -> None:
    minimum = "a" * 10
    maximum = "a" * 72
    multibyte_maximum = "密" * 24
    for password in (minimum, maximum, multibyte_maximum):
        password_hash = passwords.hash(password)
        assert password_hash.startswith(f"$2b${BCRYPT_COST:02d}$")
        assert passwords.verify(password, password_hash)
        assert not passwords.verify(password + "x", password_hash)

    with pytest.raises(PasswordPolicyError):
        passwords.hash("a" * 9)
    with pytest.raises(PasswordPolicyError):
        passwords.hash("a" * 73)
    with pytest.raises(PasswordPolicyError):
        passwords.hash("密" * 25)


def test_missing_user_runs_dummy_hash_path(passwords: PasswordHasher, monkeypatch) -> None:
    calls: list[bytes] = []

    def checked(_password: bytes, selected_hash: bytes) -> bool:
        calls.append(selected_hash)
        return False

    monkeypatch.setattr("app.auth.passwords.bcrypt.checkpw", checked)
    assert not passwords.verify("not-the-password", None)
    assert len(calls) == 1
    assert calls[0].startswith(b"$2b$12$")


def test_session_and_csrf_tokens_are_random_hashed_and_constant_time() -> None:
    tokens = SessionTokens(CSRF_KEY)
    first = tokens.generate()
    second = tokens.generate()
    assert first != second
    assert len(tokens.digest(first)) == 64
    assert first not in tokens.digest(first)
    csrf = tokens.csrf(first)
    assert tokens.valid_csrf(first, csrf, csrf)
    assert not tokens.valid_csrf(first, csrf, "wrong")
    assert not tokens.valid_csrf(first, None, csrf)


def test_login_rate_limits_use_hmac_account_and_truncated_ip_keys() -> None:
    client = MemoryRedis()
    limiter = LoginRateLimiter(client, RATE_KEY)
    email = "private-person@example.invalid"

    for _ in range(4):
        limiter.record_failure(email)
    with pytest.raises(AuthError) as account_error:
        limiter.record_failure(email)
    assert account_error.value.code == "RATE_LIMITED"
    assert all(email not in key for key in client.keys_seen)

    for _ in range(10):
        limiter.check_ip("203.0.113.44")
    with pytest.raises(AuthError):
        limiter.check_ip("203.0.113.44")
    assert "203.0.113.44" not in client.keys_seen[-1]
    assert client.keys_seen[-1].endswith("203.0.113")


def test_locked_account_rejects_correct_password(passwords: PasswordHasher) -> None:
    runtime, _, client = build_memory_runtime(passwords)
    limiter = runtime.service._rate_limiter
    for _ in range(4):
        limiter.record_failure("person@example.invalid")
    with pytest.raises(AuthError):
        limiter.record_failure("person@example.invalid")
    with pytest.raises(AuthError) as locked:
        runtime.service.login(
            "person@example.invalid",
            "correct-password",
            False,
            "127.0.0.1",
            None,
        )
    assert locked.value.code == "RATE_LIMITED"
    assert client.values


def test_redis_outage_fails_login_closed(passwords: PasswordHasher) -> None:
    runtime, _, _ = build_memory_runtime(passwords, redis_client=MemoryRedis(fail=True))
    with pytest.raises(AuthError) as caught:
        runtime.service.login(
            "person@example.invalid",
            "correct-password",
            False,
            "127.0.0.1",
            None,
        )
    assert caught.value.code == "RATE_LIMITED"
    assert caught.value.status == 429


def test_service_creates_12h_and_14d_sessions_and_enforces_rbac(passwords: PasswordHasher) -> None:
    runtime, repository, _ = build_memory_runtime(passwords)
    normal = runtime.service.login(
        "person@example.invalid",
        "correct-password",
        False,
        "127.0.0.1",
        "test",
    )
    remembered = runtime.service.login(
        "person@example.invalid",
        "correct-password",
        True,
        "127.0.0.2",
        "test",
    )
    assert 43190 <= repository.created_lifetimes[0] <= 43200
    assert 1209590 <= repository.created_lifetimes[1] <= 1209600
    principal = runtime.service.authenticate(normal.token)
    assert runtime.service.require_role(principal, "interviewer") == principal
    with pytest.raises(AuthError) as denied:
        runtime.service.require_role(principal, "owner_admin")
    assert denied.value.code == "PERM_DENIED"
    runtime.service.logout(normal.token)
    with pytest.raises(AuthError) as expired:
        runtime.service.authenticate(normal.token)
    assert expired.value.code == "AUTH_EXPIRED"
    assert remembered.token != normal.token


def test_unverified_and_invalid_credentials_are_rejected(passwords: PasswordHasher) -> None:
    runtime, _, _ = build_memory_runtime(passwords, verified=False)
    with pytest.raises(AuthError) as unverified:
        runtime.service.login(
            "person@example.invalid",
            "correct-password",
            False,
            "127.0.0.1",
            None,
        )
    assert unverified.value.code == "EMAIL_UNVERIFIED"

    runtime, _, _ = build_memory_runtime(passwords)
    with pytest.raises(AuthError) as invalid:
        runtime.service.login(
            "person@example.invalid",
            "verification-code",
            False,
            "127.0.0.1",
            None,
        )
    assert invalid.value.code == "AUTH_EXPIRED"


@pytest.mark.asyncio
async def test_auth_http_cookie_csrf_origin_and_logout(passwords: PasswordHasher) -> None:
    runtime, _, _ = build_memory_runtime(passwords)
    app = create_app(Settings(), runtime)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=ORIGIN,
    ) as client:
        login = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "email": "PERSON@example.invalid",
                "password": "correct-password",
                "remember_me": False,
            },
        )
        assert login.status_code == 204
        set_cookie = login.headers.get_list("set-cookie")
        assert any(
            item.startswith(f"{SESSION_COOKIE}=")
            and "HttpOnly" in item
            and "Secure" in item
            and "SameSite=lax" in item
            for item in set_cookie
        )
        assert any(
            item.startswith(f"{CSRF_COOKIE}=") and "HttpOnly" not in item for item in set_cookie
        )
        csrf = login.headers["X-CSRF-Token"]
        old_token = client.cookies[SESSION_COOKIE]

        rotated = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "email": "person@example.invalid",
                "password": "correct-password",
                "remember_me": False,
            },
        )
        assert rotated.status_code == 204
        assert client.cookies[SESSION_COOKIE] != old_token
        with pytest.raises(AuthError):
            runtime.service.authenticate(old_token)
        csrf = rotated.headers["X-CSRF-Token"]

        me = await client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "person@example.invalid"

        missing_csrf = await client.post("/auth/logout", headers={"Origin": ORIGIN})
        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["code"] == "PERM_DENIED"
        wrong_origin = await client.post(
            "/auth/logout",
            headers={"Origin": "https://evil.invalid", "X-CSRF-Token": csrf},
        )
        assert wrong_origin.status_code == 403

        logout = await client.post(
            "/auth/logout",
            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        )
        assert logout.status_code == 204
        expired = await client.get("/auth/me")
        assert expired.status_code == 401
        assert expired.json()["code"] == "AUTH_EXPIRED"


@pytest.mark.asyncio
async def test_cors_allows_only_configured_credentials_origin(passwords: PasswordHasher) -> None:
    runtime, _, _ = build_memory_runtime(passwords)
    app = create_app(Settings(), runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        allowed = await client.options(
            "/auth/login",
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == ORIGIN
        assert allowed.headers["access-control-allow-credentials"] == "true"

        rejected = await client.options(
            "/auth/login",
            headers={
                "Origin": "https://evil.invalid",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert rejected.status_code == 400
        assert "access-control-allow-origin" not in rejected.headers


@pytest.mark.asyncio
async def test_login_rejects_missing_origin_and_73_byte_password(
    passwords: PasswordHasher, caplog: pytest.LogCaptureFixture
) -> None:
    runtime, _, _ = build_memory_runtime(passwords)
    app = create_app(Settings(), runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
        missing_origin = await client.post(
            "/auth/login",
            json={
                "email": "person@example.invalid",
                "password": "correct-password",
                "remember_me": False,
            },
        )
        assert missing_origin.status_code == 403
        overlong = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "person@example.invalid", "password": "a" * 73, "remember_me": False},
        )
        assert overlong.status_code == 422
        multibyte_overlong = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "person@example.invalid", "password": "密" * 25, "remember_me": False},
        )
        assert multibyte_overlong.status_code == 422
        invalid = await client.post(
            "/auth/login",
            headers={"Origin": ORIGIN},
            json={
                "email": "person@example.invalid",
                "password": "wrong-password",
                "remember_me": False,
            },
        )
        assert invalid.status_code == 401
        event = next(
            record.getMessage()
            for record in reversed(caplog.records)
            if record.name == "jianli.security.auth"
            and '"event":"auth_account_failure"' in record.getMessage()
        )
        assert '"event":"auth_account_failure"' in event
        assert '"account_id":"unknown"' not in event
        assert "person@example.invalid" not in event

        client.cookies.set(SESSION_COOKIE, "not-a-valid-session")
        malformed = await client.get("/auth/me")
        assert malformed.status_code == 401


DATABASE_URL = os.environ.get("JIANLI_AUTH_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_AUTH_TEST_REDIS_URL")


@pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)
@pytest.mark.asyncio
async def test_real_postgresql_and_redis_auth_flow(passwords: PasswordHasher) -> None:
    assert DATABASE_URL and REDIS_URL
    assert make_url(DATABASE_URL).database == "jianli_auth_001_db"
    assert urlsplit(REDIS_URL).path == "/15"
    engine = create_engine(DATABASE_URL)
    redis_client = redis.Redis.from_url(REDIS_URL)
    redis_client.flushdb()
    user_id = uuid4()
    password_hash = passwords.hash("correct-password")
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,'person@example.invalid',:hash,'interviewer',true)"
            ),
            {"id": user_id, "hash": password_hash},
        )

    settings = Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        csrf_hmac_key=CSRF_KEY,
        rate_limit_hmac_key=RATE_KEY,
        allowed_origins=(ORIGIN,),
    )
    runtime = build_auth_runtime(settings)
    app = create_app(settings, runtime)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
            login = await client.post(
                "/auth/login",
                headers={"Origin": ORIGIN},
                json={
                    "email": "person@example.invalid",
                    "password": "correct-password",
                    "remember_me": False,
                },
            )
            assert login.status_code == 204
            raw_token = client.cookies[SESSION_COOKIE]
            csrf = login.headers["X-CSRF-Token"]
            with engine.connect() as connection:
                row = (
                    connection.execute(
                        text(
                            "SELECT session_token_hash,expires_at FROM auth_sessions "
                            "WHERE user_id=:user_id"
                        ),
                        {"user_id": user_id},
                    )
                    .mappings()
                    .one()
                )
            assert row["session_token_hash"] != raw_token
            assert len(row["session_token_hash"]) == 64
            remaining = (row["expires_at"] - datetime.now(UTC)).total_seconds()
            assert 43180 <= remaining <= 43200

            assert (await client.get("/auth/me")).status_code == 200
            logout = await client.post(
                "/auth/logout",
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
            )
            assert logout.status_code == 204
            assert (await client.get("/auth/me")).status_code == 401

        redis_client.flushdb()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as client:
            for _ in range(4):
                response = await client.post(
                    "/auth/login",
                    headers={"Origin": ORIGIN},
                    json={
                        "email": "person@example.invalid",
                        "password": "wrong-password",
                        "remember_me": False,
                    },
                )
                assert response.status_code == 401
            limited = await client.post(
                "/auth/login",
                headers={"Origin": ORIGIN},
                json={
                    "email": "person@example.invalid",
                    "password": "wrong-password",
                    "remember_me": False,
                },
            )
            assert limited.status_code == 429
            assert limited.json()["code"] == "RATE_LIMITED"
            assert int(limited.headers["Retry-After"]) >= 895
    finally:
        runtime.close()
        redis_client.close()
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE users CASCADE"))
        engine.dispose()

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException, Response, status

from app.core.config import Settings

SESSION_COOKIE_NAME = "ptm_session"
OAUTH_STATE_COOKIE_NAME = "ptm_oauth_state"


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _sign(value: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_signed_token(payload: dict[str, Any], secret: str, ttl_seconds: int) -> str:
    now = int(time.time())
    token_payload = {**payload, "iat": now, "exp": now + ttl_seconds}
    body = _b64encode(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    return f"{body}.{_sign(body, secret)}"


def parse_signed_token(token: str, secret: str) -> dict[str, Any]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc
    expected = _sign(body, secret)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    try:
        payload = json.loads(_b64decode(body))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return payload


def set_session_cookie(response: Response, user_id: str, settings: Settings) -> None:
    ttl_seconds = settings.access_token_ttl_minutes * 60
    token = create_signed_token({"sub": user_id}, settings.session_secret, ttl_seconds)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        domain=settings.cookie_domain,
        path="/",
    )


def create_oauth_state(provider: str, settings: Settings) -> str:
    return create_signed_token(
        {"provider": provider, "nonce": secrets.token_urlsafe(16)},
        settings.session_secret,
        ttl_seconds=10 * 60,
    )


def parse_oauth_state(token: str, provider: str, settings: Settings) -> dict[str, Any]:
    payload = parse_signed_token(token, settings.session_secret)
    if payload.get("provider") != provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    return payload


def build_url(base: str, params: dict[str, str]) -> str:
    return f"{base}?{urlencode(params)}"


import base64
import json
import secrets
from typing import Any

import httpx
from fastapi import status

from app.api.errors import api_error
from app.core.config import Settings
from app.schemas.auth import ProviderProfile


async def exchange_google_code(code: str, settings: Settings, nonce: str) -> ProviderProfile:
    redirect_uri = f"{settings.backend_base_url}/auth/google/callback"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            _raise_for_provider_status(token_response, "Google token exchange failed")
            token = token_response.json()
            id_token = token.get("id_token")
            access_token = token.get("access_token")
            if not id_token or not access_token:
                raise api_error(
                    status.HTTP_400_BAD_REQUEST,
                    "oauth_invalid_token",
                    "Google token response is missing required credentials",
                )
            tokeninfo_response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
            _raise_for_provider_status(tokeninfo_response, "Google ID token validation failed")
            claims = _google_id_token_claims(id_token, tokeninfo_response.json(), settings, nonce)
            userinfo_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            _raise_for_provider_status(userinfo_response, "Google userinfo lookup failed")
    except httpx.HTTPError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            "oauth_provider_error",
            "Google OAuth provider request failed",
        ) from exc
    userinfo = userinfo_response.json()
    if str(userinfo.get("sub")) != str(claims["sub"]):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google userinfo subject does not match the ID token",
        )
    return ProviderProfile(
        provider="google",
        provider_user_id=str(userinfo["sub"]),
        email=userinfo.get("email"),
        display_name=userinfo.get("name") or userinfo.get("email") or "Google user",
        avatar_url=userinfo.get("picture"),
    )


async def exchange_github_code(code: str, settings: Settings) -> ProviderProfile:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
            )
            _raise_for_provider_status(token_response, "GitHub token exchange failed")
            token = token_response.json()
            if "access_token" not in token:
                raise api_error(
                    status.HTTP_400_BAD_REQUEST,
                    "oauth_invalid_token",
                    "GitHub token response is missing an access token",
                )
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token['access_token']}",
            }
            user_response = await client.get("https://api.github.com/user", headers=headers)
            _raise_for_provider_status(user_response, "GitHub user lookup failed")
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise api_error(
            status.HTTP_502_BAD_GATEWAY,
            "oauth_provider_error",
            "GitHub OAuth provider request failed",
        ) from exc
    userinfo: dict[str, Any] = user_response.json()
    email = userinfo.get("email")
    if not email and emails_response.status_code == 200:
        for item in emails_response.json():
            if item.get("primary") and item.get("verified"):
                email = item.get("email")
                break
    return ProviderProfile(
        provider="github",
        provider_user_id=str(userinfo["id"]),
        email=email,
        display_name=userinfo.get("name") or userinfo.get("login") or "GitHub user",
        avatar_url=userinfo.get("avatar_url"),
    )


def _raise_for_provider_status(response: httpx.Response, message: str) -> None:
    if response.is_success:
        return
    raise api_error(status.HTTP_502_BAD_GATEWAY, "oauth_provider_error", message)


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    try:
        payload_segment = token.split(".")[1]
        padding = "=" * (-len(payload_segment) % 4)
        payload = base64.urlsafe_b64decode(f"{payload_segment}{padding}")
        claims = json.loads(payload)
    except (IndexError, ValueError, json.JSONDecodeError) as exc:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google ID token is malformed",
        ) from exc
    if not isinstance(claims, dict):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google ID token is malformed",
        )
    return claims


def _google_id_token_claims(
    id_token: str, tokeninfo: dict[str, Any], settings: Settings, nonce: str
) -> dict[str, Any]:
    claims = _decode_jwt_payload(id_token)
    if str(tokeninfo.get("aud")) != settings.google_client_id:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google ID token audience is invalid",
        )
    if str(tokeninfo.get("sub")) != str(claims.get("sub")):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google ID token subject is invalid",
        )
    token_nonce = str(tokeninfo.get("nonce") or claims.get("nonce") or "")
    if not secrets.compare_digest(token_nonce, nonce):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "oauth_invalid_token",
            "Google ID token nonce is invalid",
        )
    return claims

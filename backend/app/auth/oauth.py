from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.schemas.auth import ProviderProfile


async def exchange_google_code(code: str, settings: Settings) -> ProviderProfile:
    redirect_uri = f"{settings.backend_base_url}/auth/google/callback"
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
        token_response.raise_for_status()
        token = token_response.json()
        userinfo_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        userinfo_response.raise_for_status()
    userinfo = userinfo_response.json()
    return ProviderProfile(
        provider="google",
        provider_user_id=str(userinfo["sub"]),
        email=userinfo.get("email"),
        display_name=userinfo.get("name") or userinfo.get("email") or "Google user",
        avatar_url=userinfo.get("picture"),
    )


async def exchange_github_code(code: str, settings: Settings) -> ProviderProfile:
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
        token_response.raise_for_status()
        token = token_response.json()
        if "access_token" not in token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token missing")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token['access_token']}",
        }
        user_response = await client.get("https://api.github.com/user", headers=headers)
        user_response.raise_for_status()
        emails_response = await client.get("https://api.github.com/user/emails", headers=headers)
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


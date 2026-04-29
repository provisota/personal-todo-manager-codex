from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.oauth import exchange_github_code, exchange_google_code
from app.core.config import Settings, get_settings
from app.core.security import (
    OAUTH_STATE_COOKIE_NAME,
    build_url,
    clear_session_cookie,
    create_oauth_state,
    parse_oauth_state,
    set_session_cookie,
)
from app.db.session import get_session
from app.models.user import User
from app.repositories.auth import upsert_user_from_profile
from app.schemas.auth import AuthProvidersRead, OkResponse, ProviderProfile, TestLoginRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
    )


@router.post("/logout", response_model=OkResponse)
async def logout(response: Response, settings: Annotated[Settings, Depends(get_settings)]) -> OkResponse:
    clear_session_cookie(response, settings)
    return OkResponse()


@router.get("/providers", response_model=AuthProvidersRead)
async def providers(settings: Annotated[Settings, Depends(get_settings)]) -> AuthProvidersRead:
    return AuthProvidersRead(
        google=bool(settings.google_client_id and settings.google_client_secret),
        github=bool(settings.github_client_id and settings.github_client_secret),
        test_auth=settings.test_auth_enabled,
    )


@router.get("/{provider}/login")
async def oauth_login(provider: str, settings: Annotated[Settings, Depends(get_settings)]):
    if provider not in {"google", "github"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    state = create_oauth_state(provider, settings)
    response = RedirectResponse(_provider_authorize_url(provider, state, settings))
    response.set_cookie(
        OAUTH_STATE_COOKIE_NAME,
        state,
        max_age=600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )
    return response


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
):
    if provider not in {"google", "github"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth callback missing code")
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state mismatch")
    parse_oauth_state(state, provider, settings)

    profile = (
        await exchange_google_code(code, settings)
        if provider == "google"
        else await exchange_github_code(code, settings)
    )
    user = await upsert_user_from_profile(session, profile)
    response = RedirectResponse(f"{settings.frontend_base_url}/app")
    response.delete_cookie(OAUTH_STATE_COOKIE_NAME, domain=settings.cookie_domain, path="/")
    set_session_cookie(response, user.id, settings)
    return response


@router.post("/test-login", response_model=UserRead)
async def test_login(
    payload: TestLoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRead:
    if not settings.test_auth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user = await upsert_user_from_profile(session, ProviderProfile(**payload.model_dump()))
    set_session_cookie(response, user.id, settings)
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


def _provider_authorize_url(provider: str, state: str, settings: Settings) -> str:
    if provider == "google":
        if not settings.google_client_id:
            raise HTTPException(status_code=500, detail="Google OAuth is not configured")
        return build_url(
            "https://accounts.google.com/o/oauth2/v2/auth",
            {
                "client_id": settings.google_client_id,
                "redirect_uri": f"{settings.backend_base_url}/auth/google/callback",
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            },
        )
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth is not configured")
    return build_url(
        "https://github.com/login/oauth/authorize",
        {
            "client_id": settings.github_client_id,
            "redirect_uri": f"{settings.backend_base_url}/auth/github/callback",
            "scope": "read:user user:email",
            "state": state,
        },
    )

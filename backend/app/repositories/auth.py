from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_identity import OAuthIdentity
from app.models.user import User
from app.schemas.auth import ProviderProfile


async def upsert_user_from_profile(session: AsyncSession, profile: ProviderProfile) -> User:
    result = await session.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == profile.provider,
            OAuthIdentity.provider_user_id == profile.provider_user_id,
        )
    )
    identity = result.scalar_one_or_none()
    now = datetime.now(UTC)

    if identity:
        user = await session.get(User, identity.user_id)
        if user is None:
            raise RuntimeError("OAuth identity points to missing user")
        identity.email = profile.email
        identity.display_name = profile.display_name
        identity.avatar_url = profile.avatar_url
        user.email = profile.email or user.email
        user.display_name = profile.display_name
        user.avatar_url = profile.avatar_url
        user.last_login_at = now
        await session.commit()
        await session.refresh(user)
        return user

    user = User(
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        last_login_at=now,
    )
    session.add(user)
    await session.flush()
    session.add(
        OAuthIdentity(
            user_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            email=profile.email,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
        )
    )
    await session.commit()
    await session.refresh(user)
    return user


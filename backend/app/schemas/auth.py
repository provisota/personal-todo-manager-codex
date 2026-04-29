from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: str
    email: str | None
    display_name: str
    avatar_url: str | None


class ProviderProfile(BaseModel):
    provider: str
    provider_user_id: str
    email: EmailStr | None = None
    display_name: str = Field(min_length=1, max_length=200)
    avatar_url: str | None = None


class TestLoginRequest(BaseModel):
    provider: str = Field(pattern="^(google|github)$")
    provider_user_id: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    display_name: str = Field(min_length=1, max_length=200)
    avatar_url: str | None = None


class OkResponse(BaseModel):
    ok: bool = True


class AuthProvidersRead(BaseModel):
    google: bool
    github: bool
    test_auth: bool

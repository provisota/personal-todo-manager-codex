import asyncio
from datetime import UTC, datetime
from json import JSONDecodeError
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import SESSION_COOKIE_NAME, parse_signed_token
from app.db.session import SessionFactory, get_session_factory
from app.models.user import User
from app.schemas.ws import (
    AckMessage,
    AckOkMessage,
    AckOkPayload,
    ErrorMessage,
    ErrorPayload,
    NotificationBatchMessage,
    NotificationBatchPayload,
    SubscribeMessage,
    SubscribePayload,
)
from app.services.notifications import NotificationService

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/notifications")
async def notifications_socket(
    websocket: WebSocket,
    settings: Annotated[Settings, Depends(get_settings)],
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> None:
    user = await _authenticate_websocket(websocket, settings, session_factory)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    prefs = SubscribePayload(interval_seconds=settings.ws_notification_interval_seconds)
    async with session_factory() as session:
        await _send_batch(websocket, session, user.id, prefs)

    while True:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=prefs.interval_seconds)
            prefs = await _handle_client_message(websocket, session_factory, user.id, raw, prefs)
        except TimeoutError:
            async with session_factory() as session:
                await _send_batch(websocket, session, user.id, prefs)
        except WebSocketDisconnect:
            return


async def _authenticate_websocket(
    websocket: WebSocket, settings: Settings, session_factory: SessionFactory
) -> User | None:
    token = websocket.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = parse_signed_token(token, settings.session_secret)
    except Exception:
        return None
    async with session_factory() as session:
        return await session.get(User, payload["sub"])


async def _send_batch(
    websocket: WebSocket,
    session: AsyncSession,
    user_id: str,
    prefs: SubscribePayload,
) -> None:
    notifications = await NotificationService().get_notifications(
        session,
        user_id,
        enabled_types=list(prefs.enabled_types),
        include_acknowledged=prefs.include_acknowledged,
    )
    message = NotificationBatchMessage(
        payload=NotificationBatchPayload(
            generated_at=datetime.now(UTC),
            notifications=notifications,
        )
    )
    await websocket.send_json(message.model_dump(mode="json"))


async def _handle_client_message(
    websocket: WebSocket,
    session_factory: SessionFactory,
    user_id: str,
    raw: str,
    prefs: SubscribePayload,
) -> SubscribePayload:
    try:
        if '"type":"subscribe"' in raw.replace(" ", ""):
            message = SubscribeMessage.model_validate_json(raw)
            return message.payload
        if '"type":"ack"' in raw.replace(" ", ""):
            message = AckMessage.model_validate_json(raw)
            async with session_factory() as session:
                await NotificationService().acknowledge(session, user_id, message.payload.notification_id)
            await websocket.send_json(
                AckOkMessage(
                    payload=AckOkPayload(notification_id=message.payload.notification_id)
                ).model_dump(mode="json")
            )
            return prefs
        raise ValueError("Unsupported WebSocket message type")
    except (ValidationError, JSONDecodeError, ValueError) as exc:
        await websocket.send_json(
            ErrorMessage(
                payload=ErrorPayload(code="invalid_message", message=str(exc))
            ).model_dump(mode="json")
        )
        return prefs

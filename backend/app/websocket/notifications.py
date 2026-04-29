import asyncio
import contextlib
import json
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
    prefs_ref = {
        "value": SubscribePayload(interval_seconds=settings.ws_notification_interval_seconds),
    }
    send_lock = asyncio.Lock()
    async with session_factory() as session:
        await _send_batch(websocket, session, user.id, prefs_ref["value"], send_lock)

    receiver = asyncio.create_task(
        _receive_messages(websocket, session_factory, user.id, prefs_ref, send_lock)
    )
    periodic = asyncio.create_task(
        _send_periodic_batches(websocket, session_factory, user.id, prefs_ref, send_lock)
    )
    done, pending = await asyncio.wait({receiver, periodic}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    for task in done:
        with contextlib.suppress(WebSocketDisconnect):
            task.result()


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
    send_lock: asyncio.Lock,
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
    await _send_json(websocket, message.model_dump(mode="json"), send_lock)


async def _send_json(websocket: WebSocket, payload: dict, send_lock: asyncio.Lock) -> None:
    async with send_lock:
        await websocket.send_json(payload)


async def _send_periodic_batches(
    websocket: WebSocket,
    session_factory: SessionFactory,
    user_id: str,
    prefs_ref: dict[str, SubscribePayload],
    send_lock: asyncio.Lock,
) -> None:
    while True:
        await asyncio.sleep(prefs_ref["value"].interval_seconds)
        async with session_factory() as session:
            await _send_batch(websocket, session, user_id, prefs_ref["value"], send_lock)


async def _receive_messages(
    websocket: WebSocket,
    session_factory: SessionFactory,
    user_id: str,
    prefs_ref: dict[str, SubscribePayload],
    send_lock: asyncio.Lock,
) -> None:
    while True:
        raw = await websocket.receive_text()
        prefs_ref["value"] = await _handle_client_message(
            websocket, session_factory, user_id, raw, prefs_ref["value"], send_lock
        )


async def _handle_client_message(
    websocket: WebSocket,
    session_factory: SessionFactory,
    user_id: str,
    raw: str,
    prefs: SubscribePayload,
    send_lock: asyncio.Lock,
) -> SubscribePayload:
    try:
        envelope = json.loads(raw)
        message_type = envelope.get("type") if isinstance(envelope, dict) else None
        if message_type == "subscribe":
            message = SubscribeMessage.model_validate_json(raw)
            return message.payload
        if message_type == "ack":
            message = AckMessage.model_validate_json(raw)
            async with session_factory() as session:
                await NotificationService().acknowledge(
                    session,
                    user_id,
                    message.payload.notification_id,
                )
            await _send_json(
                websocket,
                AckOkMessage(
                    payload=AckOkPayload(notification_id=message.payload.notification_id)
                ).model_dump(mode="json"),
                send_lock,
            )
            return prefs
        raise ValueError("Unsupported WebSocket message type")
    except (ValidationError, JSONDecodeError, ValueError) as exc:
        await _send_json(
            websocket,
            ErrorMessage(
                payload=ErrorPayload(code="invalid_message", message=str(exc))
            ).model_dump(mode="json"),
            send_lock,
        )
        return prefs

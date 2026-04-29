from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


STATUS_CODES: dict[int, tuple[str, str]] = {
    status.HTTP_400_BAD_REQUEST: ("bad_request", "Bad request"),
    status.HTTP_401_UNAUTHORIZED: ("unauthorized", "Authentication required"),
    status.HTTP_403_FORBIDDEN: ("forbidden", "Forbidden"),
    status.HTTP_404_NOT_FOUND: ("not_found", "Not found"),
    status.HTTP_409_CONFLICT: ("conflict", "Conflict"),
    422: ("validation_error", "Validation failed"),
    status.HTTP_500_INTERNAL_SERVER_ERROR: ("internal_error", "Internal server error"),
}


def api_error(
    status_code: int,
    code: str,
    message: str,
    fields: list[dict[str, Any]] | None = None,
) -> HTTPException:
    detail: dict[str, Any] = {"code": code, "message": message}
    if fields:
        detail["fields"] = fields
    return HTTPException(status_code=status_code, detail=detail)


def _field_path(location: tuple[str | int, ...]) -> str:
    parts = [str(part) for part in location if part not in {"body", "query", "path", "cookie"}]
    return ".".join(parts)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and {"code", "message"}.issubset(exc.detail):
        detail = exc.detail
    else:
        default_code, default_message = STATUS_CODES.get(
            exc.status_code, ("http_error", "Request failed")
        )
        detail = {
            "code": default_code,
            "message": str(exc.detail) if exc.detail else default_message,
        }
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        {
            "field": _field_path(tuple(error["loc"])),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "validation_error",
                "message": "Validation failed",
                "fields": fields,
            }
        },
    )

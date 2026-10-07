import logging
from fastapi import Request, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.exceptions import CoreException

logger = logging.getLogger(__name__)


def _add_cors_headers(response: JSONResponse, request: Request) -> None:
    """Добавляет CORS заголовки к ответу (exception handler bypass-ит middleware)"""
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"


async def core_exception_handler(request: Request, exc: CoreException):
    """Универсальный обработчик для всех наследников CoreException"""
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers or {}
    )
    _add_cors_headers(response, request)
    return response


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic — читабельный detail + детали в extras"""
    errors = []
    first_field = None
    first_msg = None

    for error in exc.errors():
        loc = list(error["loc"])
        field = loc[-1] if loc else None
        if isinstance(field, int):
            field = loc[-2] if len(loc) > 1 else None

        errors.append({
            "location": " -> ".join(str(l) for l in loc),
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

        if first_field is None:
            first_field = field
            first_msg = error["msg"]

    field_label = str(first_field) if first_field else "Поле"
    readable_detail = f"{field_label}: {first_msg}" if first_msg else "Ошибка валидации данных"

    return JSONResponse(
        status_code=422,
        content={
            "detail": readable_detail,
            "error_code": "VALIDATION_ERROR",
            "error_type": "RequestValidationError",
            "extras": {
                "field": first_field,
                "errors": errors
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTPException (включая CoreException) с CORS заголовками"""
    if isinstance(exc, CoreException):
        content = exc.to_dict()
    else:
        content = {"detail": exc.detail}

    response = JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers or {}
    )
    _add_cors_headers(response, request)
    return response


async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик — ловит всё, что не отловлено явно. JSON вместо обрыва коннекта."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "Произошла внутренняя ошибка сервера",
            "error_type": "InternalServerError"
        }
    )
    _add_cors_headers(response, request)
    return response


def apply_exceptions_handlers(app: FastAPI) -> FastAPI:
    """Применяем глобальные обработчики исключений."""
    app.exception_handler(CoreException)(core_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(Exception)(global_exception_handler)
    return app
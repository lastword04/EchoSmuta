from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.exceptions import CoreException

async def core_exception_handler(request: Request, exc: CoreException):
    """Универсальный обработчик для всех наследников CoreException"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic"""
    errors = []
    for error in exc.errors():
        errors.append({
            "location": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "error_type": "RequestValidationError",
            "extras": {"errors": errors}
        }
    )

def apply_exceptions_handlers(app: FastAPI) -> FastAPI:
    """
    Применяем глобальные обработчики исключений.
    """
    app.exception_handler(CoreException)(core_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
        
    return app
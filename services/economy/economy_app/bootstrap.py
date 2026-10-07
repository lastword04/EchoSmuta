import sys
from pathlib import Path

# Добавляем корневую папку сервиса в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .apps.pawn_shop.scheduler import start_pricing_scheduler
from .router import apply_routes
from .settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    scheduler_task = asyncio.create_task(start_pricing_scheduler(stop_event))

    # --- Инициализация ресурсов из mining ---
    from .core.db import AsyncSessionFactory
    from .core.clients.depends import get_mining_client
    from .apps.pawn_shop.use_cases.init_resources import InitializeResourcesUseCase

    try:
        async with AsyncSessionFactory() as session:
            mining_client = get_mining_client()
            use_case = InitializeResourcesUseCase(session, mining_client)
            resources = await use_case()            
    except Exception as e:     
        import traceback
        traceback.print_exc()
    yield

    stop_event.set()
    await scheduler_task

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, docs_url="/docs", openapi_url="/docs.json")

    # Добавляем CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # список из .env
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Глобальные обработчики исключений ──

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first_error = exc.errors()[0] if exc.errors() else {}
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": f"Некорректные данные: {first_error.get('msg', 'ошибка валидации')}",
                "error_type": "ValidationError"
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "Произошла внутренняя ошибка сервера",
                "error_type": "InternalServerError"
            }
        )

    return apply_routes(app)
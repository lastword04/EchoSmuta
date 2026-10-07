# ARCHITECTURE.md - Multi-Layer Microservice Architecture Guide

This document describes the multi-layered Clean Architecture pattern for building microservices from scratch.

## Core Principles

1. **Dependency Inversion** - High-level modules don't depend on low-level modules; both depend on abstractions
2. **Single Responsibility** - Each layer/component has one reason to change
3. **Dependency Injection** - All dependencies are injected, not hardcoded
4. **Protocol-based Design** - Define interfaces (Protocols) before implementations

## Project Structure

```
service_name/
├── service_app/                    # Application package
│   ├── apps/                       # Business modules (domain)
│   │   └── module_name/
│   │       ├── adapters/           # External service clients
│   │       ├── events/             # Event handlers & publishers
│   │       ├── repositories/       # Data access layer
│   │       ├── services/           # Business logic
│   │       ├── use_cases/          # Application use cases
│   │       ├── models.py           # Database models
│   │       ├── schemas.py          # API schemas
│   │       ├── router.py           # HTTP endpoints
│   │       ├── depends.py          # Dependency injection wiring
│   │       ├── exceptions.py       # Module-specific exceptions
│   │       └── enums.py            # Domain enums
│   ├── core/                       # Shared infrastructure
│   │   ├── adapters/               # Base HTTP client
│   │   ├── repositories/           # Base repository
│   │   ├── utils/                  # Utilities
│   │   ├── db.py                   # Database setup
│   │   ├── redis.py                # Redis client
│   │   ├── use_cases.py            # Base use case protocol
│   │   └── depends.py              # Core dependencies
│   ├── main.py                     # Entry point
│   ├── bootstrap.py                # App factory
│   ├── settings.py                 # Configuration
│   ├── middleware.py               # HTTP middleware
│   ├── exceptions.py               # Global exception handlers
│   └── router.py                   # Route aggregation
├── migrations/                     # Alembic migrations
├── shared/                         # Shared code (schemas, exceptions)
├── pyproject.toml                  # Dependencies
└── .env                            # Environment variables
```

## Architecture Layers (Inside-Out)

### Layer 1: Settings (Configuration)

Configuration management using Pydantic Settings with nested configuration.

```python
# settings.py
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, List

# Nested configuration models
class DbSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    name: str
    provider: str = 'postgresql+psycopg_async'

    @property
    def dsn(self) -> str:
        return f'{self.provider}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'

class RedisSettings(BaseModel):
    host: str = 'localhost'
    port: int = 6379
    db: int = 0

    def to_connection_kwargs(self) -> dict:
        return {"host": self.host, "port": self.port, "db": self.db}

class ExternalServiceConfig(BaseModel):
    """Configuration for calling external microservices"""
    base_url: str

class BusinessConfig(BaseModel):
    """Business-specific configuration"""
    timeout_seconds: int = 180
    max_retries: int = 3

class Settings(BaseSettings):
    # Core settings
    debug: bool
    service_name: str
    secret_key: str
    
    # Nested configurations
    db: DbSettings
    redis: RedisSettings
    external_service: ExternalServiceConfig
    business: BusinessConfig

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',  # DB__HOST, REDIS__PORT
        env_prefix='SERVICE_APP_',  # SERVICE_APP__DEBUG
        case_sensitive=False,
        extra='ignore',
    )

def get_settings() -> Settings:
    return Settings()

settings = get_settings()

# For dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
```

**Environment file (.env):**
```
SERVICE_APP__DEBUG=true
SERVICE_APP__SERVICE_NAME=my-service
SERVICE_APP__SECRET_KEY=your-secret

SERVICE_APP__DB__HOST=localhost
SERVICE_APP__DB__PORT=5432
SERVICE_APP__DB__USER=postgres
SERVICE_APP__DB__PASSWORD=password
SERVICE_APP__DB__NAME=mydb

SERVICE_APP__REDIS__HOST=localhost
SERVICE_APP__REDIS__PORT=6379

SERVICE_APP__EXTERNAL_SERVICE__BASE_URL=http://localhost:8080
```

### Layer 2: Models (Database Layer)

SQLAlchemy ORM models representing database tables.

```python
# models.py
import uuid
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base

class Entity(Base):
    """Example model with standard patterns"""
    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(sa.String(50), default="active")
    external_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)
```

**Key patterns:**
- Inherit from `Base` (provides UUID `id` primary key)
- Use `Mapped[type]` for type-safe columns
- Add indexes on frequently queried fields
- Use `__table_args__` for composite constraints

### Layer 3: Schemas (Data Transfer Objects)

Pydantic models for API request/response validation.

```python
# schemas.py
import uuid
from pydantic import BaseModel, Field, ConfigDict
from shared.schemas.base import CreateBaseModel, UpdateBaseModel

# Base schema with common fields
class EntityBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    status: str = Field(default="active")

# Create schema (POST requests)
class EntityCreateSchema(EntityBaseSchema, CreateBaseModel):
    external_id: uuid.UUID | None = None

# Update schema (PUT/PATCH requests)
class EntityUpdateSchema(EntityBaseSchema, UpdateBaseModel):
    pass

# Read schema (responses)
class EntityReadSchema(EntityBaseSchema):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# Response schemas for complex data
class EntityListResponse(BaseModel):
    items: list[EntityReadSchema]
    total: int
```

**Naming convention:**
- `*BaseSchema` - Shared fields
- `*CreateSchema` - POST body (inherits `CreateBaseModel`)
- `*UpdateSchema` - PUT/PATCH body (inherits `UpdateBaseModel`)
- `*ReadSchema` - Response (includes `id`)

### Layer 4: Repositories (Data Access)

Abstract database operations. One repository per aggregate root.

```python
# repositories/entity.py
from core.repositories.base_repository import BaseRepositoryImpl, BaseRepositoryProtocol

# Protocol for dependency injection
class EntityRepositoryProtocol(BaseRepositoryProtocol[Entity, EntityReadSchema, EntityCreateSchema, EntityUpdateSchema]):
    async def get_by_slug(self, slug: str) -> EntityReadSchema: ...
    async def find_by_external_id(self, external_id: uuid.UUID) -> EntityReadSchema | None: ...

# Implementation
class EntityRepository(BaseRepositoryImpl[Entity, EntityReadSchema, EntityCreateSchema, EntityUpdateSchema], EntityRepositoryProtocol):
    
    async def get_by_slug(self, slug: str) -> EntityReadSchema:
        async with self.session as s:
            stmt = sa.select(self.model_type).where(self.model_type.slug == slug)
            result = (await s.execute(stmt)).scalar_one_or_none()
            if not result:
                raise ModelFieldNotFoundException(self.model_type, 'slug', slug)
            return self.read_schema_type.model_validate(result, from_attributes=True)

    async def find_by_external_id(self, external_id: uuid.UUID) -> EntityReadSchema | None:
        async with self.session as s:
            stmt = sa.select(self.model_type).where(self.model_type.external_id == external_id)
            result = (await s.execute(stmt)).scalar_one_or_none()
            return self.read_schema_type.model_validate(result, from_attributes=True) if result else None
```

**BaseRepositoryImpl provides:**
- `get(id)` - Get by ID
- `get_all()` - List all
- `create(schema)` - Create one
- `bulk_create(schemas)` - Create many
- `update(schema)` - Update one
- `delete(id)` - Delete by ID

### Layer 5: Services (Business Logic)

Encapsulate business rules and domain logic.

```python
# services/entity.py
from repositories.entity import EntityRepositoryProtocol

class EntityServiceProtocol(Protocol):
    async def get_by_slug(self, slug: str) -> EntityReadSchema: ...
    async def create(self, data: EntityCreateSchema) -> EntityReadSchema: ...
    async def process_complex_business_logic(self, entity_id: uuid.UUID) -> EntityReadSchema: ...

class EntityService(EntityServiceProtocol):
    def __init__(self, repository: EntityRepositoryProtocol):
        self.repository = repository

    async def get_by_slug(self, slug: str) -> EntityReadSchema:
        return await self.repository.get_by_slug(slug)

    async def create(self, data: EntityCreateSchema) -> EntityReadSchema:
        # Business validation before creation
        existing = await self.repository.find_by_external_id(data.external_id)
        if existing:
            raise EntityAlreadyExistsError(data.external_id)
        
        return await self.repository.create(data)

    async def process_complex_business_logic(self, entity_id: uuid.UUID) -> EntityReadSchema:
        # Complex business rules here
        entity = await self.repository.get(entity_id)
        # ... business logic ...
        return entity
```

**Rules:**
- One service per domain aggregate
- Inject repositories, not sessions
- Keep methods focused on single responsibility
- Throw domain-specific exceptions

### Layer 6: Adapters (External Services)

HTTP clients for inter-service communication.

```python
# adapters/external_service.py
from core.adapters.base_http import BaseHttpClientImpl

class ExternalServiceClientProtocol(Protocol):
    async def get_resource(self, resource_id: uuid.UUID) -> ExternalResourceSchema: ...
    async def update_resource(self, resource_id: uuid.UUID, data: dict) -> StatusSchema: ...

class ExternalServiceClient(BaseHttpClientImpl, ExternalServiceClientProtocol):
    def __init__(self, base_url: str, timeout: float = 15.0):
        super().__init__(
            base_url=base_url,
            target_service="external-service",
            permissions=["resource:read", "resource:write"],
            timeout=timeout
        )
    
    async def get_resource(self, resource_id: uuid.UUID) -> ExternalResourceSchema:
        return await self.request(
            "GET",
            f"/api/resources/{resource_id}",
            response_model=ExternalResourceSchema
        )
    
    async def update_resource(self, resource_id: uuid.UUID, data: dict) -> StatusSchema:
        return await self.request(
            "PUT",
            f"/api/resources/{resource_id}",
            response_model=StatusSchema,
            json=data
        )
```

### Layer 7: Use Cases (Application Layer)

Orchestrate services for specific user actions. One use case = one user goal.

```python
# use_cases/create_entity.py
from core.use_cases import UseCaseProtocol

class CreateEntityUseCaseProtocol(UseCaseProtocol[EntityReadSchema]):
    async def __call__(self, user: UserSchema, data: EntityCreateSchema) -> EntityReadSchema: ...

class CreateEntityUseCase(CreateEntityUseCaseProtocol):
    def __init__(
        self,
        entity_service: EntityServiceProtocol,
        external_client: ExternalServiceClientProtocol,
        event_publisher: EventPublisherProtocol
    ):
        self.entity_service = entity_service
        self.external_client = external_client
        self.event_publisher = event_publisher

    async def __call__(self, user: UserSchema, data: EntityCreateSchema) -> EntityReadSchema:
        # 1. Authorization check
        if not user.can_create_entities:
            raise PermissionDeniedError("Cannot create entities")

        # 2. Fetch external data if needed
        external_data = await self.external_client.get_resource(data.external_id)

        # 3. Enrich data
        data.external_name = external_data.name

        # 4. Create entity
        entity = await self.entity_service.create(data)

        # 5. Publish event
        await self.event_publisher.publish("entity_created", {"id": str(entity.id)})

        return entity
```

**Use case structure:**
1. Authorization/validation
2. Fetch required data
3. Execute business logic
4. Publish events (if needed)
5. Return result

### Layer 8: Dependency Injection (depends.py)

Wire all components together using FastAPI's DI system.

```python
# depends.py
from fastapi import Depends
from core.db import AsyncSession, get_async_session
from settings import Settings, get_settings

# Repository (private, use __ prefix)
def __get_entity_repository(
    session: AsyncSession = Depends(get_async_session)
) -> EntityRepositoryProtocol:
    return EntityRepository(session=session)

# Service
def get_entity_service(
    repository: EntityRepositoryProtocol = Depends(__get_entity_repository)
) -> EntityServiceProtocol:
    return EntityService(repository=repository)

# External adapter
def get_external_service_client(
    settings: Settings = Depends(get_settings)
) -> ExternalServiceClientProtocol:
    return ExternalServiceClient(base_url=settings.external_service.base_url)

# Event publisher
def get_event_publisher(
    redis: Redis = Depends(get_redis_client)
) -> EventPublisherProtocol:
    return EventPublisher(redis)

# Use case (composes multiple dependencies)
def get_create_entity_use_case(
    entity_service: EntityServiceProtocol = Depends(get_entity_service),
    external_client: ExternalServiceClientProtocol = Depends(get_external_service_client),
    event_publisher: EventPublisherProtocol = Depends(get_event_publisher)
) -> CreateEntityUseCaseProtocol:
    return CreateEntityUseCase(entity_service, external_client, event_publisher)
```

**Naming convention:**
- `__get_*_repository()` - Private repository factories
- `get_*_service()` - Public service factories
- `get_*_client()` - Adapter factories
- `get_*_use_case()` - Use case factories

### Layer 9: Router (API Layer)

HTTP endpoints that delegate to use cases.

```python
# router.py
from fastapi import APIRouter, Depends, Path

router = APIRouter(prefix='/api/entities', tags=['Entities'])

@router.post('/', response_model=EntityReadSchema, status_code=201)
async def create_entity(
    data: EntityCreateSchema,
    user: UserSchema = Depends(get_current_user),
    use_case: CreateEntityUseCaseProtocol = Depends(get_create_entity_use_case)
) -> EntityReadSchema:
    return await use_case(user, data)

@router.get('/{entity_id}', response_model=EntityReadSchema)
async def get_entity(
    entity_id: uuid.UUID = Path(...),
    user: UserSchema = Depends(get_current_user),
    use_case: GetEntityUseCaseProtocol = Depends(get_get_entity_use_case)
) -> EntityReadSchema:
    return await use_case(user, entity_id)

@router.get('/', response_model=EntityListResponse)
async def list_entities(
    user: UserSchema = Depends(get_current_user),
    use_case: ListEntitiesUseCaseProtocol = Depends(get_list_entities_use_case)
) -> EntityListResponse:
    return await use_case(user)
```

**Router rules:**
- Inject use cases, never services or repositories
- Define `response_model` for documentation
- Define `status_code` for non-200 responses
- Keep endpoints thin - logic in use cases

## Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                        HTTP Request                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Router                                                      │
│  - Validates request body (Schema)                           │
│  - Authenticates user (Dependency)                           │
│  - Delegates to Use Case                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Use Case                                                    │
│  - Authorization checks                                      │
│  - Orchestrates business flow                                │
│  - Coordinates multiple services                             │
│  - Publishes events                                          │
└──────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Service      │ │    Service      │ │    Adapter      │
│ (Business Logic)│ │ (Business Logic)│ │ (External Call) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
            │                 │
            ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│   Repository    │ │   Repository    │
│ (Database CRUD) │ │ (Database CRUD) │
└─────────────────┘ └─────────────────┘
            │                 │
            └────────┬────────┘
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                      Database                                │
└──────────────────────────────────────────────────────────────┘
```

## Bootstrap (Application Startup)

```python
# bootstrap.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_database()
    await start_event_handlers()
    yield
    # Shutdown
    await stop_event_handlers()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Service Name",
        lifespan=lifespan
    )
    app = apply_routes(apply_exceptions_handlers(apply_middleware(app)))
    return app
```

```python
# main.py
from bootstrap import create_app

app = create_app()

if __name__ == "__main__":
    # Run with Granian ASGI server
    import granian
    granian.Granian(
        "service_app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        interface="asgi"
    ).serve()
```

## Exception Handling

Define domain-specific exceptions inheriting from base exception:

```python
# exceptions.py
from shared.exceptions import CoreException
from fastapi import status

class EntityNotFoundException(CoreException):
    def __init__(self, entity_id: uuid.UUID):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
            error_code="ENTITY_NOT_FOUND",
            error_type="EntityNotFoundException",
            extras={"entity_id": str(entity_id)}
        )

class EntityAlreadyExistsError(CoreException):
    def __init__(self, slug: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entity with slug '{slug}' already exists",
            error_code="ENTITY_ALREADY_EXISTS",
            error_type="EntityAlreadyExistsError",
            extras={"slug": slug}
        )
```

## Data Initialization Pattern

Services use initializators to seed configuration data at startup:

```python
# initializator.py
async def initialize_app(session: AsyncSession):
    await initialize_items(session)
    await initialize_city_trading_settings(session)
    await initialize_city_trading_buy_settings(session)
    # ... more initializators
```

**Initializator logic:**

1. Fetch current records from DB
2. Compare count with expected defaults
3. If counts match → already initialized, skip
4. If DB empty → create all default records
5. If DB has partial data → raise error (manual cleanup needed)

Example:

```python
class InitializeCityTradingShopSettingsUseCase:
    async def __call__(self):
        current = await self.service.get_all()
        expected = self._get_default_settings()
        
        if len(current) == len(expected):
            return current  # Already initialized
        
        if len(current) != 0:
            raise ValueError("Count mismatch - manual cleanup needed")
        
        return await self.service.bulk_create(expected)
    
    def _get_default_settings(self):
        # Define all levels for all locations
        return [
            CityTradingShopSettingsCreateSchema(
                location_slug="1.9.pharmacy",
                level=0,
                capacity=200,
                tax=0.075,
                price_up_level=53
            ),
            # ... more records
        ]
```

Adding new location:

1. Add records to _get_default_settings()
2. Restart service
3. If error → clean DB and restart

## Template System

Text templates provide localized messages for user notifications.

Structure:
shared/
└── system_messages.json

**Template service:**

```python
class ItemTemplateService:
    LOCATION_KEYS = {
        "1.9.pharmacy": "pharmacy",
        "1.27.trade-hall": "trade_hall",
    }
    
    def get_shop_purchase_message(self, location_slug, number, city_name):
        return self._get_template(
            location_slug,
            "shop",
            "purchase_self",
            number=number,
            city_name=city_name
        )
    
    def _get_template(self, location_slug, section, template_name, **kwargs):
        location_key = self.LOCATION_KEYS.get(location_slug)
        if not location_key:
            raise ValueError(f"Unknown location: {location_slug}")
        
        return self.template_service.get_template_by_path(
            ["items", "locations", location_key, section, template_name],
            **kwargs
        )
```

JSON structure:

```json
{
  "items": {
    "locations": {
      "pharmacy": {
        "shop": {
          "purchase_self": "Вы приобрели Аптеку №{number} в городе {city_name}.",
          "license_renewal": "Вы обновили лицензию аптеки до {end_license}"
        }
      }
    }
  }
}
```

Templates loaded at startup - must restart service after changes.

## Event-Driven Architecture

Services communicate via events for loose coupling.

Event publisher:

```python
class ItemEvents:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def publish_message(self, event: ItemMessageEventSchema):
        await self.redis.publish("item_messages", event.model_dump_json())
```

Use case with events:

```python
class CreateCityShopUseCase:
    def __init__(
        self,
        service: CityTradingShopServiceProtocol,
        event_publisher: ItemEventsProtocol
    ):
        self.service = service
        self.event_publisher = event_publisher
    
    async def __call__(self, user, data):
        # 1. Create entity
        shop = await self.service.create(data)
        
        # 2. Publish private message
        await self.event_publisher.publish_message(
            ItemMessageEventSchema(
                event_type="shop_purchase_private",
                character_id=user.character_id,
                content=f"Вы приобрели лавку №{shop.number}",
                scope=ItemMessageScope.PRIVATE
            )
        )
        
        # 3. Publish public message
        await self.event_publisher.publish_message(
            ItemMessageEventSchema(
                event_type="shop_purchase_public",
                character_id=user.character_id,
                content=f"{user.name} открыл лавку №{shop.number}",
                scope=ItemMessageScope.CITY
            )
        )
        
        return shop
```

**Event scopes:**
- `PRIVATE` - visible only to character
- `CITY` - visible to all in location
- `GLOBAL` - visible to all players

## Transaction Boundaries

Single transaction:

```python
class CreateEntityUseCase:
    async def __call__(self, user, data):
        async with self.repository.session.begin():
            # All operations in one transaction
            entity = await self.service.create(data)
            await self.service.update_related(entity.id)
            return entity
```

Cross-service calls:

```python
class CreateEntityUseCase:
    async def __call__(self, user, data):
        async with self.repository.session.begin():
            # 1. Create in DB
            entity = await self.service.create(data)
            
            # 2. Call external service (outside transaction!)
            await self.external_client.notify(entity.id)
            
            # 3. If external call fails → DB still committed
            # Need compensating transaction or manual cleanup
        
        return entity
```

Best practice:

- Keep DB transactions short
- Call external services outside transactions
- Implement compensating transactions for external calls
- Log external calls for manual recovery if needed

## Summary Checklist

When creating a new microservice:

1. **Setup** - Create project structure with `service_app/`, `core/`, `apps/`
2. **Settings** - Define configuration with nested Pydantic models
3. **Models** - Create SQLAlchemy models for each table
4. **Schemas** - Define Base/Create/Update/Read schemas
5. **Repositories** - Implement data access with Protocol + Impl
6. **Services** - Add business logic layer
7. **Adapters** - Create HTTP clients for external services
8. **Use Cases** - Orchestrate business operations
9. **depends.py** - Wire dependencies with DI
10. **Router** - Define HTTP endpoints
11. **Bootstrap** - Setup app factory and lifespan
12. **Exceptions** - Add domain-specific error classes
13. **Initializators** - Seed configuration data
14. **Templates** - Add user-facing messages
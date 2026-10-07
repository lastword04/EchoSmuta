# AGENTS.md - EchoSmyta Services

This document provides guidelines for agentic coding agents working in this repository.

## Project Overview

EchoSmyta is a Python FastAPI monorepo with multiple microservices:
- `auth/` - Authentication service (port 8080)
- `chat/` - Chat service (port 8081)
- `users/` - User management service (port 8082)
- `email/` - Email notification service (port 8083)
- `file-storage/` - File storage service (port 8084)
- `captcha-service/` - Captcha service (port 8085)
- `forum/` - Forum service
- `characters/` - Character management service
- `mining/` - Mining service
- `economy/` - Economy service (port 8090)
- `shared/` - Shared code (schemas, exceptions, utilities)

Infrastructure directories (not services):
- `docker/` - Docker compose and container configs
- `scripts/` - Utility/deploy scripts

Tech stack: FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Celery, Granian, Pydantic, Alembic

## Build/Lint/Test Commands

### Running Services

Each service can be run using:
```bash
# From within a service directory (e.g., auth/)
python -m auth_app.main
# or
./run.sh
```

### Database Migrations

```bash
# Create migration (from service directory)
alembic revision --autogenerate -m "description"

# Run migrations
./migrate.sh
# or
alembic upgrade head

# Create and apply in one step
./make_migrate_and_migrate.sh
```

### Virtual Environment

Services use `uv` for dependency management. Each service has its own `.venv`:
```bash
# Activate venv (in service directory)
source .venv/bin/activate
```

### Dependencies

Install/update dependencies:
```bash
uv sync
```

## Code Style Guidelines

### Imports

Order imports alphabetically within groups:
1. Standard library
2. Third-party packages
3. Local imports (relative imports using `..` or `.`)

Example:
```python
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.auth import UserReadSchema
from ...core.db import get_async_session
```

Use explicit relative imports (e.g., `from ...core.db import`).

### Project Structure

```
service/
├── service_app/
│   ├── apps/
│   │   └── module/
│   │       ├── __init__.py
│   │       ├── models.py          # SQLAlchemy models
│   │       ├── schemas.py         # Pydantic request/response schemas
│   │       ├── router.py          # FastAPI router
│   │       ├── depends.py         # Dependency injection
│   │       ├── exceptions.py     # Module-specific exceptions
│   │       ├── repositories/     # Database access layer
│   │       ├── services/         # Business logic
│   │       ├── adapters/         # External service clients
│   │       ├── use_cases/        # Use case implementations
│   │       └── utils/            # Utilities
│   ├── core/
│   │   ├── db.py                 # Database setup
│   │   ├── redis.py              # Redis client
│   │   ├── repositories/         # Base repository classes
│   │   └── utils/                # Core utilities
│   ├── main.py
│   ├── settings.py
│   └── bootstrap.py
├── migrations/
├── shared/
│   ├── schemas/                   # Shared Pydantic schemas
│   ├── exceptions.py             # Core exceptions
│   └── services/                 # Shared services
└── pyproject.toml
```

### Naming Conventions

- **Files**: snake_case (e.g., `user_service.py`, `base_repository.py`)
- **Classes**: PascalCase (e.g., `UserRepository`, `AuthService`)
- **Functions/variables**: snake_case (e.g., `get_user`, `user_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)
- **Protocols**: `<Name>Protocol` (e.g., `UserRepositoryProtocol`)
- **Use Cases**: `<Name>UseCase` (e.g., `LoginUseCase`)

### Type Annotations

Use type hints for all function parameters and return types:
```python
async def get_user(user_id: uuid.UUID) -> UserReadSchema | None:
    ...

def process_data(items: list[str], options: dict[str, Any]) -> int:
    ...
```

Use `Annotated` for FastAPI dependencies:
```python
Session = Annotated[AsyncSession, Depends(get_async_session)]
```

### Pydantic Models

- Use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- Use `Field()` for field customization
- Use base models from `shared/schemas/base.py`:
  - `CreateBaseModel` for create schemas
  - `UpdateBaseModel` for update schemas

Example:
```python
from pydantic import BaseModel, ConfigDict, Field
from shared.schemas.base import CreateBaseModel

class UserCreateSchema(CreateBaseModel):
    email: str
    username: str
    password: str

class UserReadSchema(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    model_config = ConfigDict(from_attributes=True)
```

### Database Models

- Use `Base` from `core.db` as parent class
- Use UUID as primary key type
- Use async SQLAlchemy patterns

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str]
```

### Error Handling

Use custom exceptions inheriting from `CoreException` in `shared/exceptions.py`:

```python
from shared.exceptions import CoreException
from fastapi import status

class UserNotFoundException(CoreException):
    def __init__(self, user_id: uuid.UUID):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
            error_code="USER_NOT_FOUND",
            error_type="UserNotFoundException",
            extras={"user_id": str(user_id)}
        )
```

Common exceptions in `shared/exceptions.py`:
- `CoreException` - Base exception
- `InvalidTokenError`
- `PermissionDeniedError`
- `CharacterIsNotOnlineError`

Service-specific exceptions in `core/utils/exceptions.py`:
- `ModelNotFoundException`
- `ModelAlreadyExistsError`
- `ValidationError`
- `ExternalServiceError` and variants

### Dependency Injection

Use Protocol classes for dependency injection interfaces:

```python
from typing import Protocol, runtime_checkable
from typing_extensions import Self

@runtime_checkable
class UserRepositoryProtocol(Protocol):
    async def get(self, user_id: uuid.UUID) -> UserReadSchema: ...
    async def create(self, data: UserCreateSchema) -> UserReadSchema: ...

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID) -> UserReadSchema:
        # Implementation
        ...

def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepositoryProtocol:
    return UserRepository(session)
```

Use `UseCaseProtocol` from `core/use_cases.py` for use cases:
```python
from ...core.use_cases import UseCaseProtocol

class LoginUseCaseProtocol(UseCaseProtocol[AuthSchema]):
    async def __call__(self, request: Request, data: LoginSchema) -> AuthSchema: ...

class LoginUseCase(LoginUseCaseProtocol):
    def __init__(self, service: AuthServiceProtocol):
        self.service = service

    async def __call__(self, request: Request, data: LoginSchema) -> AuthSchema:
        # Implementation
        ...
```

### Settings

Use Pydantic Settings with nested configuration:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

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

class Settings(BaseSettings):
    debug: bool
    db: DbSettings

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
    )

settings = Settings()
```

Environment variables use double underscore for nesting: `AUTH_SERVICE_APP__DEBUG=true`

### Routing

Define routers with prefix and tags:
```python
router = APIRouter(prefix='/api/users', tags=['Users'])

@router.get('/{user_id}', response_model=UserReadSchema)
async def get_user(user_id: uuid.UUID) -> UserReadSchema:
    ...
```

### Async/Await

Always use async/await. Use `async with` for context managers:
```python
async with self.session as s:
    result = await s.execute(statement)
```

### Testing

No test framework is currently configured. When adding tests:
- Use `pytest` with `pytest-asyncio`
- Place tests in `tests/` directory
- Use fixtures for database sessions
- Mock external services

Example test structure:
```
service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_module/
│       ├── __init__.py
│       └── test_feature.py
```

Run tests:
```bash
pytest tests/
pytest tests/test_module/test_feature.py::test_function  # Single test
```

### Migration Commands

Generate migration:
```bash
alembic revision --autogenerate -m "Add user table"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

### Git Conventions

- Write meaningful commit messages
- Create feature branches for new features
- Use conventional commits format (optional): `feat:`, `fix:`, `refactor:`, `docs:`

### Environment Files

Each service has a `.env` file (not committed). Example structure:
```
SERVICE_NAME=auth
DEBUG=true
BASE_URL=http://localhost:8080
SECRET_KEY=your-secret-key

DB__HOST=localhost
DB__PORT=5432
DB__USER=postgres
DB__PASSWORD=password
DB__NAME=auth_db

REDIS__HOST=localhost
REDIS__PORT=6379

CORS_ORIGINS=http://localhost:3000
TRUSTED_HOSTS=localhost,127.0.0.1
```

## Project-Specific Patterns

### Initializators (Data Seeding)

Each service has initializators/ directory for seeding configuration data:

```python
# apps/module/use_cases/initializators/init_settings.py
class InitializeSettingsUseCase:
    def __init__(self, service: SettingsServiceProtocol):
        self.service = service

    async def __call__(self):
        current = await self.service.get_all()
        expected = self._get_default_settings()
        
        if len(current) == len(expected):
            return current
        
        if len(current) != 0:
            raise ValueError("Settings count mismatch")
        
        return await self.service.bulk_create(expected)
    
    def _get_default_settings(self):
        # Define all configuration records
        return [...]
```

Called from: initializator.py during app startup
Adding new locations:
Add to _get_default_settings() in both init_city_trading_shop_settings.py and init_city_trading_shop_buy_settings.py
Add to LOCATION_KEYS in item_templates.py
Add templates to shared/system_messages.json

### Template System

Text templates stored in shared/system_messages.json:

```json
{
  "items": {
    "locations": {
      "pharmacy": {
        "shop": {
          "purchase_self": "Вы приобрели Аптеку №{number} в городе {city_name}."
        }
      }
    }
  }
}
```

Adding new location templates:
Add to LOCATION_KEYS dict in item_templates.py
Add JSON block to shared/system_messages.json
Restart service (templates loaded at startup)

### Event-Driven Architecture

Services publish events for cross-service communication:

```python
# use_cases/some_use_case.py
class CreateEntityUseCase:
    def __init__(self, event_publisher: ItemEventsProtocol):
        self.event_publisher = event_publisher
    
    async def __call__(self, user, data):
        entity = await self.service.create(data)
        
        await self.event_publisher.publish_message(
            ItemMessageEventSchema(
                event_type="entity_created",
                character_id=user.character_id,
                location_slug=entity.location_slug,
                content="Your entity was created",
                scope=ItemMessageScope.PRIVATE
            )
        )
        return entity
```

### Clean Architecture Workflow

Typical feature implementation order:

1. Model → apps/module/models.py
2. Schema → apps/module/schemas.py
3. Repository → apps/module/repositories/entity.py
4. Service → apps/module/services/entity.py
5. Use Case → apps/module/use_cases/create_entity.py
6. Depends → apps/module/depends.py (wire dependencies)
7. Router → apps/module/router.py (expose endpoint)
8. Initializator → if config data needed
9. Templates → if user-facing messages needed

### Common Pitfalls

**Database state after errors:**
When use case fails mid-transaction (e.g., after creating entity but before publishing event):
- Entity created in DB
- External service calls completed
- No automatic rollback

**Solution**: Check DB state, manually clean up, or implement compensating transactions.

**Template errors:**
If template key missing in system_messages.json:
- Service crashes with KeyError
- Must restart service after adding templates

**Initializator count mismatch:**
If DB has partial data from previous failed init:
- Initializator raises ValueError
- Must manually clean DB table or delete all records

## Troubleshooting

### "Unknown item template location slug"
Cause: Location not registered in template system
Fix:
1. Add to LOCATION_KEYS in item_templates.py
2. Add template block to shared/system_messages.json
3. Restart service

### "City trading shop settings count is incorrect"
Cause: DB has partial initialization data
Fix:

```sql
-- Check current state
SELECT location_slug, COUNT(*) FROM city_trading_shop_settings GROUP BY location_slug;

-- Clean if needed
DELETE FROM city_trading_shop_settings WHERE location_slug = 'new.location';
DELETE FROM city_trading_shop_buy_settings WHERE location_slug = 'new.location';

-- Restart service to re-initialize
```

### Frontend 404 errors in console
Cause: Browser logs HTTP errors before JavaScript handles them
Example:

```javascript
// itemService.js
getCityShop: async () => {
  try {
    const response = await itemApiInstance.get('/city-shop');
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null; // Correctly handled
    }
    throw error;
  }
}
```

Browser console shows red 404 even though code handles it. This is normal browser behavior, not a bug.

### React.StrictMode double API calls
Cause: Development mode runs effects twice to detect side effects
Impact: API calls happen twice in dev, once in production
Solution: Ignore in development, works correctly in production build

## Feature Implementation Checklist

### Adding New Trade Location (e.g., "1.28.magic-shop")

**Backend:**
- [ ] Add to TRADE_LOCATIONS list if needed
- [ ] Create migration for any new tables
- [ ] Add to _get_default_settings() in init_city_trading_shop_settings.py
- [ ] Add to _get_default_settings() in init_city_trading_shop_buy_settings.py
- [ ] Add to LOCATION_KEYS in item_templates.py
- [ ] Add template block to shared/system_messages.json
- [ ] Restart service

**Frontend:**
- [ ] Add to TRADE_LOCATIONS in locations.js
- [ ] Add to tradeConfig.js with buttons and labels
- [ ] Create view components if needed
- [ ] Update TradeHallPage or CityTradeLocation to handle new views
- [ ] Test all tabs and flows

**Testing:**
- [ ] Purchase shop/tent
- [ ] Extend license
- [ ] Level up
- [ ] Buy/sell items
- [ ] Check messages in chat



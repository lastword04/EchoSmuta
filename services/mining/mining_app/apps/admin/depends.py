from fastapi import Depends

from shared.permissions import ensure_admin
from shared.schemas.auth import UserTokenDataReadSchema

from ...core.db import AsyncSession, get_async_session
from ...core.depends import get_user_token_payload
from ...settings import Settings, get_settings
from ..items.adapters.characters import CharacterServiceClientProtocol
from ..items.deps.adapters import get_character_service_client
from ..items.deps.character import get_character_item_service
from ..items.deps.items import get_equipment_service
from ..items.services.character.character_items import CharacterItemServiceProtocol
from ..items.services.character.equipment import EquipmentServiceProtocol
from ..resources.depends import get_character_resource_service, get_redis_publisher
from ..resources.events.publisher import RedisPublisherProtocol
from ..resources.services.character_resource import CharacterResourceServiceProtocol
from .repositories.admin_mutations import AdminMutationRepository
from .repositories.admin_read import AdminReadRepository
from .services.admin_mutations import AdminMutationService, AdminMutationServiceProtocol
from .services.admin_read import AdminReadService


def require_admin(token: UserTokenDataReadSchema = Depends(get_user_token_payload)) -> UserTokenDataReadSchema:
    ensure_admin(token)
    return token


def get_admin_read_repository(session: AsyncSession = Depends(get_async_session)) -> AdminReadRepository:
    return AdminReadRepository(session)


def get_admin_read_service(
    repository: AdminReadRepository = Depends(get_admin_read_repository),
    characters: CharacterServiceClientProtocol = Depends(get_character_service_client),
) -> AdminReadService:
    return AdminReadService(repository, characters)


def get_admin_mutation_repository(session: AsyncSession = Depends(get_async_session)) -> AdminMutationRepository:
    return AdminMutationRepository(session)


def get_admin_mutation_service(
    repository: AdminMutationRepository = Depends(get_admin_mutation_repository),
    item_service: CharacterItemServiceProtocol = Depends(get_character_item_service),
    equipment_service: EquipmentServiceProtocol = Depends(get_equipment_service),
    resource_service: CharacterResourceServiceProtocol = Depends(get_character_resource_service),
    characters: CharacterServiceClientProtocol = Depends(get_character_service_client),
    publisher: RedisPublisherProtocol = Depends(get_redis_publisher),
    settings: Settings = Depends(get_settings),
) -> AdminMutationServiceProtocol:
    return AdminMutationService(repository, item_service, equipment_service, resource_service, characters, publisher, settings)

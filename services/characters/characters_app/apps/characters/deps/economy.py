from fastapi import Depends
from ....core.db import AsyncSession, get_async_session
from ..repositories.character.characters import CharacterRepositoryProtocol
from ..repositories.economy.currency_operations import (
    CharacterCurrencyOperationRepositoryProtocol,
    CharacterCurrencyOperationRepository,
)
from ..repositories.economy.transfer_value_settings import (
    TransferValueCharactersSettingsRepositoryProtocol,
    TransferValueCharactersSettingsRepository,
)
from ..services.character.characters import (
    UpdateCharacterDucatsServiceProtocol,
    UpdateCharacterDucatsService,
)
from ..services.economy.character_transfer import (
    CharacterTransferServiceProtocol,
    CharacterTransferService,
)
from ..services.economy.currency_operations import (
    CharacterCurrencyOperationServiceProtocol,
    CharacterCurrencyOperationService,
)
from ..services.economy.transfer_value_settings import (
    TransferValueCharactersSettingsServiceProtocol,
    TransferValueCharactersSettingsService,
)
from ..use_cases.characters.update_ducats import (
    UpdateCharacterDucatsUseCaseProtocol,
    UpdateCharacterDucatsUseCase,
)
from ..use_cases.economy.transfer_value_characters import (
    TransferValueCharacterUseCaseProtocol,
    TransferValueCharacterUseCase,
)
from ..use_cases.economy.get_transfer_rules import (
    GetTransferValueCharactersSettingsUseCaseProtocol,
    GetTransferValueCharactersSettingsUseCase,
)
from ..use_cases.initializators.init_transfer_value_settings import (
    InitializeTransferValueSettingsUseCaseProtocol,
    InitializeTransferValueSettingsUseCase,
)
from .valid import __get_character_repository


def __get_transfer_value_characters_settings_repository_dep(session: AsyncSession = Depends(get_async_session)) -> TransferValueCharactersSettingsRepositoryProtocol:
    """
    Функция для получения репозитория настроек стоимости переноса персонажей.
    """
    return TransferValueCharactersSettingsRepository(session=session)


def get_transfer_value_characters_settings_service_dep(repository: TransferValueCharactersSettingsRepositoryProtocol = Depends(__get_transfer_value_characters_settings_repository_dep)) -> TransferValueCharactersSettingsServiceProtocol:
    """
    Функция для получения сервиса настроек стоимости переноса персонажей.
    """
    return TransferValueCharactersSettingsService(repository=repository)


def get_character_update_ducats_service(repository: CharacterRepositoryProtocol = Depends(__get_character_repository)) -> UpdateCharacterDucatsServiceProtocol:
    return UpdateCharacterDucatsService(repository=repository)


def get_character_update_ducats_use_case(service: UpdateCharacterDucatsServiceProtocol = Depends(get_character_update_ducats_service)) -> UpdateCharacterDucatsUseCaseProtocol:
    return UpdateCharacterDucatsUseCase(service=service)


def get_character_currency_operation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> CharacterCurrencyOperationRepositoryProtocol:
    return CharacterCurrencyOperationRepository(session=session)


def get_character_currency_operation_service(
    repository: CharacterCurrencyOperationRepositoryProtocol = Depends(get_character_currency_operation_repository),
) -> CharacterCurrencyOperationServiceProtocol:
    return CharacterCurrencyOperationService(repository=repository)


def get_character_transfer_service(character_repository: CharacterRepositoryProtocol = Depends(__get_character_repository),
                                   transfer_value_settings_service: TransferValueCharactersSettingsServiceProtocol = Depends(get_transfer_value_characters_settings_service_dep)
                                   ) -> CharacterTransferServiceProtocol:
    return CharacterTransferService(character_repository=character_repository, transfer_value_settings_service=transfer_value_settings_service)


def get_transfer_value_character_use_case(service: CharacterTransferServiceProtocol = Depends(get_character_transfer_service)) -> TransferValueCharacterUseCaseProtocol:
    return TransferValueCharacterUseCase(service=service)


def get_transfer_rules_use_case(
        service: TransferValueCharactersSettingsServiceProtocol = Depends(get_transfer_value_characters_settings_service_dep)
                                ) -> GetTransferValueCharactersSettingsUseCaseProtocol:
    return GetTransferValueCharactersSettingsUseCase(service=service)


def get_initialize_transfer_value_settings_use_case_dep(session: AsyncSession) -> InitializeTransferValueSettingsUseCaseProtocol:
    repo = __get_transfer_value_characters_settings_repository_dep(session=session)
    service = get_transfer_value_characters_settings_service_dep(repository=repo)
    return InitializeTransferValueSettingsUseCase(service=service)

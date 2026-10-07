import uuid
import logging
from decimal import Decimal
from typing import Protocol, Tuple
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema
from .....core.utils.exceptions import PermissionDeniedError, ModelNotFoundException
from ...models import Character
from ...repositories.character.characters import CharacterRepositoryProtocol
from ...schemas import (
    CharacterTransferRequestSchema, CharacterUpdateDBSchema, 
    TransferValueCharactersSettingsReadSchema, TransferResult
)
from ...exceptions import CannotDetachOnlineCharacterError, InsufficientLevelError, InsufficientFundsError
from .transfer_value_settings import TransferValueCharactersSettingsServiceProtocol

logger = logging.getLogger(__name__)


class CharacterTransferServiceProtocol(Protocol):
    async def transfer_character(
        self: Self,
        request: CharacterTransferRequestSchema,
        user_id: uuid.UUID
    ) -> TransferResult:
        ...

class CharacterTransferService(CharacterTransferServiceProtocol):
    def __init__(
        self, 
        character_repository: CharacterRepositoryProtocol,
        transfer_value_settings_service: TransferValueCharactersSettingsServiceProtocol
    ):
        self.character_repository = character_repository
        self.transfer_value_settings_service = transfer_value_settings_service

    async def transfer_character(
        self,
        request: CharacterTransferRequestSchema,
        user_id: uuid.UUID
    ) -> TransferResult:
        """Transfer currency between characters with validation and tax application."""
        
        transaction_id = uuid.uuid4()
        
        logger.info(
            f"Starting character transfer - Transaction: {transaction_id}, "
            f"User: {user_id}, From: {request.from_character_id}, To: {request.to_character_id}, "
            f"Gold: {request.offered_gold}, Ducats: {request.offered_ducats}"
        )
        
        try:
            # Get characters and settings
            from_character, to_character, settings = await self._get_transfer_dependencies(
                request.from_character_id, 
                request.to_character_id, 
                user_id
            )
            
            # Validate transfer
            await self._validate_transfer(from_character, to_character, request, settings, user_id)
            
            # Execute transfer with tax
            result = await self._execute_transfer(
                from_character, to_character, request, settings, transaction_id
            )
            
            logger.info(
                f"Character transfer completed successfully - Transaction: {transaction_id}, "
                f"Transferred Gold: {result.transferred_gold}, Transferred Ducats: {result.transferred_ducats}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Character transfer failed - Transaction: {transaction_id}, "
                f"User: {user_id}, Error: {str(e)}"
            )
            raise

    async def _get_transfer_dependencies(
        self, 
        from_character_id: uuid.UUID, 
        to_character_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Tuple[CharacterReadSchema, CharacterReadSchema, TransferValueCharactersSettingsReadSchema]:
        """Get all required data for transfer operation."""
        
        logger.debug(f"Fetching transfer dependencies for user {user_id}")
        
        try:
            from_character = await self.character_repository.get(from_character_id)
            to_character = await self.character_repository.get(to_character_id)
            settings = (await self.transfer_value_settings_service.get_all())[0]
            
            logger.debug(
                f"Dependencies fetched - From character level: {from_character.level}, "
                f"To character level: {to_character.level}, Min transfer level: {settings.min_transfer_level}"
            )
            
            return from_character, to_character, settings
            
        except Exception as e:
            logger.error(f"Failed to fetch transfer dependencies: {str(e)}")
            raise

    async def _validate_transfer(
        self, 
        from_character: CharacterReadSchema, 
        to_character: CharacterReadSchema, 
        request: CharacterTransferRequestSchema, 
        settings: TransferValueCharactersSettingsReadSchema, 
        user_id: uuid.UUID
    ) -> None:
        """Validate all transfer conditions."""
        
        logger.debug(f"Starting transfer validation for user {user_id}")
        
        # Validate character ownership and status
        self._validate_character_ownership_and_status(from_character, to_character, user_id)
        
        # Validate characters are not online
        # Комментируем, так как такое обновление возможно пока без ошибок в онлайне
        # self._validate_characters_offline(from_character, to_character)
        
        # Validate not same character
        self._validate_different_characters(from_character, to_character)
        
        # Validate character levels
        self._validate_character_levels(from_character, to_character, settings)
        
        # Validate currency amounts
        self._validate_currency_transfer(from_character, request, settings)
        
        logger.debug("Transfer validation completed successfully")

    def _validate_character_ownership_and_status(
        self, 
        from_character: CharacterReadSchema, 
        to_character: CharacterReadSchema, 
        user_id: uuid.UUID
    ) -> None:
        """Validate characters belong to user and are active."""
        
        if from_character.user_id != user_id or not from_character.is_active:
            logger.warning(
                f"Invalid from_character access - User: {user_id}, "
                f"Character: {from_character.id}, Owner: {from_character.user_id}, "
                f"Active: {from_character.is_active}"
            )
            # --- МОДИФИКАЦИЯ: Добавляем field в extras ---
            raise ModelNotFoundException(
                Character, 
                from_character.id,
                detail="Персонаж-отправитель не найден или не принадлежит вам",
                error_code="CHARACTER_NOT_FOUND", # Изменяем error_code
                extras={"field": "from_character_id"} # Добавляем поле
            )
            
        if to_character.user_id != user_id or not to_character.is_active:
            logger.warning(
                f"Invalid to_character access - User: {user_id}, "
                f"Character: {to_character.id}, Owner: {to_character.user_id}, "
                f"Active: {to_character.is_active}"
            )
            # --- МОДИФИКАЦИЯ: Добавляем field в extras ---
            raise ModelNotFoundException(
                Character, 
                to_character.id,
                detail="Персонаж-получатель не найден или не принадлежит вам",
                error_code="CHARACTER_NOT_FOUND", # Изменяем error_code
                extras={"field": "to_character_id"} # Добавляем поле
            )

    def _validate_characters_offline(self, from_character: CharacterReadSchema, to_character: CharacterReadSchema) -> None:
        """Validate both characters are offline."""
        
        if from_character.is_online:
            logger.warning(f"Attempted transfer from online character: {from_character.id}")
            # --- МОДИФИКАЦИЯ: Изменяем error_code и добавляем field ---
            raise CannotDetachOnlineCharacterError(
                character_id=from_character.id, 
                character_name=from_character.name,
                detail="Отправитель должен быть в оффлайне",
                error_code="CHARACTER_ONLINE", # Изменяем error_code
                extras={"field": "from_character_id"} # Добавляем поле
            )
            
        if to_character.is_online:
            logger.warning(f"Attempted transfer to online character: {to_character.id}")
            # --- МОДИФИКАЦИЯ: Изменяем error_code и добавляем field ---
            raise CannotDetachOnlineCharacterError(
                character_id=to_character.id, 
                character_name=to_character.name,
                detail="Получатель должен быть в оффлайне",
                error_code="CHARACTER_ONLINE", # Изменяем error_code
                extras={"field": "to_character_id"} # Добавляем поле
            )

    def _validate_different_characters(self, from_character: CharacterReadSchema, to_character: CharacterReadSchema) -> None:
        """Validate transfer is between different characters."""
        
        if from_character.id == to_character.id:
            logger.warning(f"Attempted self-transfer for character: {from_character.id}")
            # --- МОДИФИКАЦИЯ: Изменяем error_code ---
            # PermissionDeniedError обычно имеет error_code="PERMISSION_DENIED"
            # Нужно либо создать новое исключение, либо передать новый error_code
            # Создадим новое исключение или переопределим error_code
            raise PermissionDeniedError(
                detail="Нельзя переводить самому себе",
                error_code="TRANSFER_TO_SELF", # Изменяем error_code
                extras={"field": "to_character_id"} # Добавляем поле, если нужно
            )


    def _validate_character_levels(
        self, 
        from_character: CharacterReadSchema, 
        to_character: CharacterReadSchema, 
        settings: TransferValueCharactersSettingsReadSchema
    ) -> None:
        """Validate both characters meet minimum level requirement."""
        
        if from_character.level <= settings.min_transfer_level:
            logger.warning(
                f"From character level too low - Character: {from_character.id}, "
                f"Level: {from_character.level}, Required: {settings.min_transfer_level}"
            )
            # --- МОДИФИКАЦИЯ: Изменяем error_code и добавляем field ---
            raise InsufficientLevelError(
                required_amount=settings.min_transfer_level,
                current_amount=from_character.level,
                detail=f"Уровень отправителя слишком низкий. Требуется уровень выше {settings.min_transfer_level}",
                error_code="CHARACTER_LEVEL_TOO_LOW", # Изменяем error_code
                extras={"field": "from_character_id"} # Добавляем поле
            )
            
        if to_character.level <= settings.min_transfer_level:
            logger.warning(
                f"To character level too low - Character: {to_character.id}, "
                f"Level: {to_character.level}, Required: {settings.min_transfer_level}"
            )
            # --- МОДИФИКАЦИЯ: Изменяем error_code и добавляем field ---
            raise InsufficientLevelError(
                required_amount=settings.min_transfer_level,
                current_amount=to_character.level,
                detail=f"Уровень получателя слишком низкий. Требуется уровень выше {settings.min_transfer_level}",
                error_code="CHARACTER_LEVEL_TOO_LOW", # Изменяем error_code
                extras={"field": "to_character_id"} # Добавляем поле
            )

    def _validate_currency_transfer(
        self, 
        from_character: CharacterReadSchema, 
        request: CharacterTransferRequestSchema, 
        settings: TransferValueCharactersSettingsReadSchema
    ) -> None:
        """Validate currency amounts for transfer."""
        
        if request.offered_gold > Decimal("0"):
            self._validate_gold_transfer(from_character, request.offered_gold, settings)

        if request.offered_ducats > Decimal("0"):
            self._validate_ducats_transfer(from_character, request.offered_ducats, settings)

    def _validate_gold_transfer(self, from_character: CharacterReadSchema, offered_gold: Decimal, settings: TransferValueCharactersSettingsReadSchema) -> None:
        """Validate gold transfer amount."""
        
        if offered_gold < settings.min_transfer_gold:
            logger.warning(
                f"Gold amount below minimum - Character: {from_character.id}, "
                f"Offered: {offered_gold}, Required: {settings.min_transfer_gold}"
            )
            raise InsufficientFundsError(
                required_amount=settings.min_transfer_gold,
                current_amount=offered_gold,
                currency="gold",
                detail=f"Сумма золота меньше минимальной ({settings.min_transfer_gold})",
                error_code="AMOUNT_BELOW_MINIMUM", # Изменяем error_code
                extras={"field": "gold", "min_value": settings.min_transfer_gold} # Добавляем поле и min_value
            )
            
        if offered_gold > from_character.gold:
            logger.warning(
                f"Insufficient gold - Character: {from_character.id}, "
                f"Requested: {offered_gold}, Available: {from_character.gold}"
            )
            # --- МОДИФИКАЦИЯ: Добавляем field ---
            raise InsufficientFundsError(
                required_amount=offered_gold,
                current_amount=from_character.gold,
                currency="gold",
                detail=f"Недостаточно золота. Требуется: {offered_gold}, доступно: {from_character.gold}",
                extras={"field": "gold"} # Добавляем поле
            )

    def _validate_ducats_transfer(self, from_character: CharacterReadSchema, offered_ducats: Decimal, settings: TransferValueCharactersSettingsReadSchema) -> None:
        """Validate ducats transfer amount."""
        
        # offered_ducats уже Decimal, min_transfer_ducats тоже
        offered_ducats_dec = offered_ducats
        min_transfer_ducats = settings.min_transfer_ducats
        
        if offered_ducats_dec < min_transfer_ducats:
            logger.warning(
                f"Ducats amount below minimum - Character: {from_character.id}, "
                f"Offered: {offered_ducats}, Required: {min_transfer_ducats}"
            )
            raise InsufficientFundsError(
                required_amount=min_transfer_ducats,
                current_amount=offered_ducats_dec,
                currency="ducats",
                detail=f"Сумма дукатов меньше минимальной ({min_transfer_ducats:.2f})",
                error_code="AMOUNT_BELOW_MINIMUM",
                extras={"field": "ducats", "min_value": min_transfer_ducats}
            )
            
        if offered_ducats_dec > from_character.ducats:
            logger.warning(
                f"Insufficient ducats - Character: {from_character.id}, "
                f"Requested: {offered_ducats_dec}, Available: {from_character.ducats}"
            )
            raise InsufficientFundsError(
                required_amount=offered_ducats_dec,
                current_amount=from_character.ducats,
                currency="ducats",
                detail=f"Недостаточно дукатов. Требуется: {offered_ducats_dec:.2f}, доступно: {from_character.ducats:.2f}",
                extras={"field": "ducats"}
            )
        
        # Теперь обе части Decimal — умножение работает
        tax_rate = Decimal(str(settings.transfer_tax_percentage))
        transfer_ducats_with_tax = offered_ducats_dec * (Decimal("1") + tax_rate)

        if from_character.ducats < transfer_ducats_with_tax:
            logger.warning(
                f"Ducats transfer would result in negative balance - Character: {from_character.id}, "
                f"Current: {from_character.ducats}, Offered: {offered_ducats_dec}, Tax: {transfer_ducats_with_tax - offered_ducats_dec}"
            )
            raise InsufficientFundsError(
                required_amount=transfer_ducats_with_tax,
                current_amount=from_character.ducats,
                currency="ducats",
                detail=f"Недостаточно дукатов с учетом налога. Требуется: {transfer_ducats_with_tax:.2f}, доступно: {from_character.ducats:.2f}",
                extras={"field": "ducats"}
            )

    async def _execute_transfer(
        self, 
        from_character: CharacterReadSchema, 
        to_character: CharacterReadSchema, 
        request: CharacterTransferRequestSchema, 
        settings: TransferValueCharactersSettingsReadSchema,
        transaction_id: uuid.UUID
    ) -> TransferResult:
        """Execute the actual currency transfer with tax calculation."""
        
        logger.debug(
            f"Executing transfer - Transaction: {transaction_id}, "
            f"Tax rate: {settings.transfer_tax_percentage}"
        )
        
        # Calculate amounts after tax
        transfer_ducats = request.offered_ducats
        
        tax_ducats = request.offered_ducats * Decimal(str(settings.transfer_tax_percentage))
        
        logger.debug(
            f"Transfer amounts calculated - Gold: without tax, "
            f"Ducats: {transfer_ducats} (tax: {tax_ducats})"
        )
        
        try:
            # Update from character (subtract offered amounts)
            from_character_new_gold = (from_character.gold - request.offered_gold).quantize(Decimal('0.01'))
            from_character_new_ducats = (from_character.ducats - transfer_ducats - tax_ducats).quantize(Decimal('0.01'))

            from_character_update = CharacterUpdateDBSchema(
                gold=from_character_new_gold,
                ducats=from_character_new_ducats,
                **from_character.model_dump(exclude={"gold", "ducats"})
            )
            await self.character_repository.update(from_character_update)
            
            logger.debug(f"From character updated - ID: {from_character.id}")
            
            # Update to character (add transfer amounts after tax)
            to_character_new_gold = (to_character.gold + request.offered_gold).quantize(Decimal('0.01'))
            to_character_new_ducats = (to_character.ducats + transfer_ducats).quantize(Decimal('0.01'))

            to_character_update = CharacterUpdateDBSchema(
                gold=to_character_new_gold,
                ducats=to_character_new_ducats,
                **to_character.model_dump(exclude={"gold", "ducats"})
            )
            await self.character_repository.update(to_character_update)
            
            logger.debug(f"To character updated - ID: {to_character.id}")
            
            return TransferResult(
                success=True,
                transferred_gold=request.offered_gold,
                transferred_ducats=transfer_ducats,
                tax_applied_ducats=tax_ducats,
                from_character_id=from_character.id,
                to_character_id=to_character.id,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            logger.error(f"Failed to execute transfer - Transaction: {transaction_id}, Error: {str(e)}")
            raise
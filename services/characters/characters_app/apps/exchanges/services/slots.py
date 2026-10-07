import uuid
import logging
from typing import Protocol, Tuple
from typing_extensions import Self
from decimal import Decimal
from shared.schemas.characters import CharacterUpdateSchema, CharacterReadSchema
from shared.schemas.base import PaginationSchema
from ....core.utils.exceptions import ModelNotFoundException, PermissionDeniedError
from ..adapters.characters import GetMainCharacterAdapterProtocol, UpdateCharacterAdapterProtocol
from ..models import Slot
from ..repositories.slots import SlotRepositoryProtocol
from .exchanges import ExchangeSettingsServiceProtocol
from ..schemas import (
    SlotCreateSchema,
    SlotCreateDBSchema,
    SlotReadSchema,
    ExchangeSettingsReadSchema,
    SlotPaginationResultSchema,
    BuySlotResponse,
    SlotRequestSchema
)
from ..enums import Currency
from ..exceptions import (
    CannotTransactionWithOnlineCharacterError, InvalidCourseError,
    InsufficientFundsError, SlotLimitExceededError, AmountBelowMinimumError
) 

logger = logging.getLogger(__name__)

class CreateSlotServiceProtocol(Protocol):
    repository: SlotRepositoryProtocol
    exchange_settings: ExchangeSettingsServiceProtocol
    character_service: GetMainCharacterAdapterProtocol
    character_update_service: UpdateCharacterAdapterProtocol

    async def create(self: Self, slot: SlotRequestSchema, user_id: uuid.UUID) -> SlotReadSchema:
        ...


class CreateSlotService(CreateSlotServiceProtocol):
    def __init__(
        self, 
        repository: SlotRepositoryProtocol,
        exchange_settings: ExchangeSettingsServiceProtocol,
        character_service: GetMainCharacterAdapterProtocol,
        character_update_service: UpdateCharacterAdapterProtocol
    ) -> None:
        self.repository = repository
        self.exchange_settings = exchange_settings
        self.character_service = character_service
        self.character_update_service = character_update_service

    async def create(self: Self, slot: SlotRequestSchema, user_id: uuid.UUID) -> SlotReadSchema:
        """Create a new slot with validation and tax calculation."""
        
        slot_id = uuid.uuid4()
        logger.info(
            f"Starting slot creation - Slot ID: {slot_id}, User: {user_id}, "
            f"Sell: {slot.currency}, Value: {slot.value}, Course: {slot.course}"
        )
        
        try:
            # Get dependencies
            character, settings = await self._get_slot_creation_dependencies(user_id)
            
            # Validate slot parameters
            self._validate_slot_creation(slot, character, settings)
            
            # Calculate costs and taxes
            gold_levied, ducats_levied = await self._calculate_slot_costs(slot, character, settings)
            
            # Create slot and update character
            created_slot = await self._execute_slot_creation(
                slot, character, gold_levied, ducats_levied, slot_id
            )
            
            logger.info(
                f"Slot creation completed - Slot ID: {slot_id}, "
                f"Gold levied: {gold_levied}, Ducats levied: {ducats_levied}"
            )
            
            return created_slot
            
        except Exception as e:
            logger.error(f"Slot creation failed - Slot ID: {slot_id}, User: {user_id}, Error: {str(e)}")
            raise

    async def _get_slot_creation_dependencies(
        self, 
        user_id: uuid.UUID
    ) -> Tuple[CharacterReadSchema, ExchangeSettingsReadSchema]:
        """Get character and settings for slot creation."""
        
        logger.debug(f"Fetching slot creation dependencies for user {user_id}")
        
        try:
            character = await self.character_service.get_main_character_by_user_id(user_id)
            settings = (await self.exchange_settings.get_all())[0]
            
            logger.debug(
                f"Dependencies fetched - Character ID: {character.id}, "
                f"Character gold: {character.gold}, Character ducats: {character.ducats}"
            )
            
            return character, settings
            
        except Exception as e:
            logger.error(f"Failed to fetch slot creation dependencies: {str(e)}")
            raise

    def _validate_slot_creation(
        self,
        slot: SlotRequestSchema,
        character: CharacterReadSchema,
        settings: ExchangeSettingsReadSchema
    ) -> None:
        """Validate all slot creation conditions."""
        
        logger.debug(f"Starting slot creation validation for character {character.id}")
        
        # комментируем, так как пока что не происходит ошибок при обновлении персонажа с монетами при оффлайне
        # self._validate_offline_character(character)
        # Validate currency amounts and limits
        self._validate_currency_limits(slot, settings)
        
        # Validate exchange course
        self._validate_exchange_course(slot, settings)
        
        logger.debug("Slot creation validation completed successfully")

    def _validate_offline_character(self, character: CharacterReadSchema) -> None:
        """Ensure character is offline for transactions."""
        
        if character.is_online:
            logger.warning(f"Character {character.id} is online, cannot proceed with transaction")
            raise CannotTransactionWithOnlineCharacterError(
                detail="Character must be offline to perform this action",
                character_id=character.id,
                character_name=character.name
            )

    def _validate_currency_limits(self, slot: SlotRequestSchema, settings: ExchangeSettingsReadSchema) -> None:
        """Validate currency amounts against minimum and maximum limits."""
        
        if slot.currency == Currency.DUCATS:
            self._validate_ducats_limits(slot.value, settings)
        elif slot.currency == Currency.GOLD:
            self._validate_gold_limits(slot.value, settings)

    def _validate_ducats_limits(self, ducats: Decimal, settings: ExchangeSettingsReadSchema) -> None:
        """Validate ducats amount against limits."""
        
        if ducats < settings.min_ducats_on_slot:
            logger.warning(
                f"Ducats amount below minimum - Offered: {ducats}, "
                f"Required: {settings.min_ducats_on_slot}"
            )
            raise AmountBelowMinimumError(
                detail=f"Minimum ducats to create slot is {settings.min_ducats_on_slot}",
                field="ducats",
                min_value=settings.min_ducats_on_slot,
                actual_value=ducats,
                currency="ducats"
            )
            
        if ducats > settings.max_ducats_on_slot:
            logger.warning(
                f"Ducats amount above maximum - Offered: {ducats}, "
                f"Maximum: {settings.max_ducats_on_slot}"
            )
            raise SlotLimitExceededError(
                detail=f"Maximum ducats to create slot is {settings.max_ducats_on_slot}",
                field="ducats",
                max_value=settings.max_ducats_on_slot,
                actual_value=ducats
            )
    
    def _validate_gold_limits(self, gold: Decimal, settings: ExchangeSettingsReadSchema) -> None:
        """Validate gold amount against limits."""
        
        if gold < settings.min_gold_on_slot:
            logger.warning(
                f"Gold amount below minimum - Offered: {gold}, "
                f"Required: {settings.min_gold_on_slot}"
            )
            raise AmountBelowMinimumError(
                detail=f"Minimum gold to create slot is {settings.min_gold_on_slot}",
                field="gold",
                min_value=settings.min_gold_on_slot,
                actual_value=gold,
                currency="gold"
            )
            
        if gold > settings.max_gold_on_slot:
            logger.warning(
                f"Gold amount above maximum - Offered: {gold}, "
                f"Maximum: {settings.max_gold_on_slot}"
            )
            raise SlotLimitExceededError(
                detail=f"Maximum gold to create slot is {settings.max_gold_on_slot}",
                field="gold",
                max_value=settings.max_gold_on_slot,
                actual_value=gold
            )

    def _validate_exchange_course(self, slot: SlotRequestSchema, settings: ExchangeSettingsReadSchema) -> None:
        """Validate exchange course (ducats to gold ratio)."""
        
        if slot.course < settings.min_course_on_gold:
            logger.warning(
                f"Exchange course too low - Course: {slot.course}, "
                f"Minimum: {settings.min_course_on_gold}"
            )
            raise InvalidCourseError(
                detail=f"Course is too low. Minimum course is {settings.min_course_on_gold} ducats per gold",
                min_course=settings.min_course_on_gold,
                max_course=settings.max_course_on_gold,
                actual_course=slot.course
            )
            
        if slot.course > settings.max_course_on_gold:
            logger.warning(
                f"Exchange course too high - Course: {slot.course}, "
                f"Maximum: {settings.max_course_on_gold}"
            )
            raise InvalidCourseError(
                detail=f"Course is too high. Maximum course is {settings.max_course_on_gold} ducats per gold",
                min_course=settings.min_course_on_gold,
                max_course=settings.max_course_on_gold,
                actual_course=slot.course
            )

    async def _calculate_slot_costs(
        self,
        slot: SlotRequestSchema,
        character: CharacterReadSchema,
        settings: ExchangeSettingsReadSchema
    ) -> Tuple[int, Decimal]:
        """Calculate total costs including taxes for slot creation."""
        
        logger.debug(f"Calculating slot costs for character {character.id}")
        
        gold_levied = 0
        ducats_levied = Decimal('0')
        
        if slot.currency == Currency.DUCATS:
            currency, ducats_levied = self._calculate_ducats_slot_costs(slot, character, settings)
        elif slot.currency == Currency.GOLD:
            gold_levied, ducats_levied = self._calculate_gold_slot_costs(slot, character, settings)
        
        logger.debug(
            f"Slot costs calculated - Gold levied: {gold_levied}, "
            f"Ducats levied: {ducats_levied}"
        )
        
        return gold_levied, ducats_levied

    def _calculate_ducats_slot_costs(
        self,
        slot: SlotRequestSchema,
        character: CharacterReadSchema,
        settings: ExchangeSettingsReadSchema
    ) -> Tuple[float, Decimal]:
        """Calculate costs for ducats-based slot."""
        
        # Calculate ducats with tax
        ducats_levied = slot.value * Decimal(str(1 + settings.seller_on_ducats_tax))
        
        # Validate character has enough ducats
        if character.ducats < ducats_levied:
            logger.warning(
                f"Insufficient ducats for slot creation - Character: {character.id}, "
                f"Required: {ducats_levied}, Available: {character.ducats}"
            )
            raise InsufficientFundsError(
                detail="Not enough ducats to create slot including tax",
                required_amount=float(ducats_levied),
                current_amount=character.ducats,
                currency="ducats"
            )
        
        return 0, ducats_levied

    def _calculate_gold_slot_costs(
        self,
        slot: SlotRequestSchema,
        character: CharacterReadSchema,
        settings: ExchangeSettingsReadSchema
    ) -> Tuple[int, Decimal]:
        """Calculate costs for gold-based slot."""
        
        # Validate character has enough gold
        if character.gold < slot.value:
            logger.warning(
                f"Insufficient gold for slot creation - Character: {character.id}, "
                f"Required: {slot.value}, Available: {character.gold}"
            )
            raise InsufficientFundsError(
                detail="Not enough gold to create slot",
                required_amount=slot.value,
                current_amount=character.gold,
                currency="gold"
            )
        
        # Calculate ducats tax (15% от суммы сделки в дукатах)
        ducats_levied = (slot.value * slot.course * Decimal(str(settings.seller_on_ducats_tax))).quantize(Decimal('0.01'))
        
        # Validate character has enough ducats for tax
        if character.ducats < ducats_levied:
            logger.warning(
                f"Insufficient ducats for tax - Character: {character.id}, "
                f"Required: {ducats_levied}, Available: {character.ducats}"
            )
            raise InsufficientFundsError(
                detail="Not enough ducats to pay tax for creating slot",
                required_amount=float(ducats_levied),
                current_amount=character.ducats,
                currency="ducats"
            )
        
        return slot.value, ducats_levied

    async def _execute_slot_creation(
        self,
        slot: SlotRequestSchema,
        character: CharacterReadSchema,
        gold_levied: int,
        ducats_levied: Decimal,
        slot_id: uuid.UUID
    ) -> SlotReadSchema:
        """Execute the actual slot creation and character update."""
        
        logger.debug(f"Executing slot creation - Slot ID: {slot_id}")
        
        try:
            # Create slot in database
            gold = 0
            ducats = 0 
            if slot.currency == Currency.DUCATS:
                gold = Decimal(str(slot.value / slot.course)).quantize(Decimal('1'))  
                ducats = slot.value
            if slot.currency == Currency.GOLD:
                ducats = (slot.value * slot.course).quantize(Decimal('0.01'))
                gold = slot.value
            db_slot = SlotCreateDBSchema(gold=gold,
                                        ducats=ducats,
                                        buy_for=slot.currency.opposite(),
                                        seller_id=character.id)
            created_slot = await self.repository.create(db_slot)
            
            logger.debug(f"Slot created in database - ID: {created_slot.id}")
            
            # Update character with new balances
            new_gold = character.gold - Decimal(str(gold_levied))
            new_ducats = (character.ducats - ducats_levied).quantize(Decimal('0.01'))
            
            await self.character_update_service.update_character(
                character.id,
                CharacterUpdateSchema(
                    gold=new_gold,
                    ducats=new_ducats,
                    **character.model_dump(exclude={"gold", "ducats"})
                )
            )
            
            logger.debug(
                f"Character updated - ID: {character.id}, "
                f"New gold: {new_gold}, New ducats: {new_ducats}"
            )
            
            return SlotReadSchema(
                **created_slot.model_dump(exclude={"seller_id"}), 
                is_owner=True
            )
            
        except Exception as e:
            logger.error(f"Failed to execute slot creation - Slot ID: {slot_id}, Error: {str(e)}")
            raise


class DeleteSlotServiceProtocol(Protocol):
    repository: SlotRepositoryProtocol
    character_service: GetMainCharacterAdapterProtocol
    character_update_service: UpdateCharacterAdapterProtocol
    exchange_settings: ExchangeSettingsServiceProtocol


    async def delete(self: Self, slot_id: uuid.UUID, user_id: uuid.UUID) -> None:
        ...

class DeleteSlotService(DeleteSlotServiceProtocol):
    def __init__(
        self,
        repository: SlotRepositoryProtocol,
        character_service: GetMainCharacterAdapterProtocol,
        character_update_service: UpdateCharacterAdapterProtocol,
        exchange_settings: ExchangeSettingsServiceProtocol,
    ) -> None:
        self.repository = repository
        self.character_service = character_service
        self.character_update_service = character_update_service
        self.exchange_settings = exchange_settings

    async def delete(self: Self, slot_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a slot if owned by the user's main character."""
        
        logger.info(f"Starting slot deletion - Slot ID: {slot_id}, User: {user_id}")
        
        try:
            # Get user's main character
            character = await self.character_service.get_main_character_by_user_id(user_id)
            
            # убираем это, так как пока при списывании валюты нет ошибок, если персонаж онлайн
            # if character.is_online:
            #     logger.warning(f"Character {character.id} is online, cannot proceed with transaction")
            #     raise CannotTransactionWithOnlineCharacterError(
            #         detail="Character must be offline to perform this action",
            #         character_id=character.id,
            #         character_name=character.name
            #     )
            settings = (await self.exchange_settings.get_all())[0]
            # Get slot and validate ownership
            slot = await self.repository.get(slot_id)
            if slot.seller_id != character.id:
                logger.warning(
                    f"Unauthorized slot deletion attempt - Slot ID: {slot_id}, "
                    f"Character ID: {character.id}"
                )
                raise ModelNotFoundException(Slot, slot_id)
            
            add_gold = 0
            add_ducats = Decimal('0')

            # Так как до этого указывался курс при продаже, то при удалении слота возврат делаем обратный созданию
            if slot.buy_for == Currency.GOLD:
                add_ducats = (slot.ducats * Decimal(str(1 + settings.seller_on_ducats_tax))).quantize(Decimal('0.01'))
               
            elif slot.buy_for == Currency.DUCATS:
                add_gold = slot.gold
                add_ducats = (slot.ducats * Decimal(str(settings.seller_on_ducats_tax))).quantize(Decimal('0.01'))

            changed_ducats = (character.ducats + add_ducats).quantize(Decimal('0.01'))
            # Update character balances
            await self.character_update_service.update_character(
                character.id,
                CharacterUpdateSchema(
                    gold=character.gold + add_gold,
                    ducats=changed_ducats,
                    **character.model_dump(exclude={"gold", "ducats"})
                )
            )
            # Delete the slot
            await self.repository.delete(slot_id)
            
            logger.info(f"Slot deletion completed - Slot ID: {slot_id}")
            
        except Exception as e:
            logger.error(f"Slot deletion failed - Slot ID: {slot_id}, User: {user_id}, Error: {str(e)}")
            raise

class GetSlotsServiceProtocol(Protocol):
    repository: SlotRepositoryProtocol
    character_service: GetMainCharacterAdapterProtocol

    async def paginate(self: Self, pagination: PaginationSchema, buy_for: Currency, user_id: uuid.UUID) -> SlotPaginationResultSchema:

        ...

class GetSlotsService(GetSlotsServiceProtocol):
    def __init__(
        self,
        repository: SlotRepositoryProtocol,
        character_service: GetMainCharacterAdapterProtocol
    ) -> None:
        self.repository = repository
        self.character_service = character_service

    async def paginate(self: Self, pagination: PaginationSchema, buy_for: Currency, user_id: uuid.UUID) -> SlotPaginationResultSchema:
        """Paginate slots with ownership indication."""

        logger.info(f"Starting slot pagination - User: {user_id}, Limit: {pagination.limit}, Offset: {pagination.offset}")

        try:
            # Get user's main character
            character = await self.character_service.get_main_character_by_user_id(user_id)
            
            # Paginate slots from repository
            slots = await self.repository.paginate(search=buy_for.value, 
                                                   search_by=["buy_for"], 
                                                   sorting=["-ducats"] if buy_for == Currency.DUCATS else ["-gold", "created_at"],
                                                   pagination=pagination,
                                                   user=None,
                                                   policies=["can_view_all_slots"]
                                                   )
            

            # Map to read schemas with ownership info
            slot_schemas = [
                SlotReadSchema(
                    is_owner=(slot.seller_id == character.id),
                    **slot.model_dump(exclude={"seller_id"}),
                ) for slot in slots.objects
            ]
            
            logger.info(f"Slot pagination completed - User: {user_id}, Retrieved: {len(slot_schemas)} slots")
            
            return SlotPaginationResultSchema(objects=slot_schemas, count=slots.count)
            
        except Exception as e:
            logger.error(f"Slot pagination failed - User: {user_id}, Error: {str(e)}")
            raise


class BuySlotServiceProtocol(Protocol):
    repository: SlotRepositoryProtocol
    character_service: GetMainCharacterAdapterProtocol
    character_update_service: UpdateCharacterAdapterProtocol

    async def buy(self: Self, slot_id: uuid.UUID, user_id: uuid.UUID) -> BuySlotResponse:
        ...

class BuySlotService(BuySlotServiceProtocol):
    def __init__(self: Self, repository: SlotRepositoryProtocol, character_service: GetMainCharacterAdapterProtocol, character_update_service: UpdateCharacterAdapterProtocol):
        self.repository = repository
        self.character_service = character_service
        self.character_update_service = character_update_service

    async def buy(self: Self, slot_id: uuid.UUID, user_id: uuid.UUID) -> BuySlotResponse:
        """Buy a slot if not owned by the user's main character."""
        
        logger.info(f"Starting slot purchase - Slot ID: {slot_id}, User: {user_id}")
        
        # Get user's main character
        character = await self.character_service.get_main_character_by_user_id(user_id)
        
        # убираем это, так как пока при списывании валюты нет ошибок, если персонаж онлайн
        # if character.is_online:
        #     logger.warning(f"Character {character.id} is online, cannot proceed with transaction")
        #     raise CannotTransactionWithOnlineCharacterError(
        #         detail="Character must be offline to perform this action",
        #         character_id=character.id,
        #         character_name=character.name
        #     )

        # Get slot and validate ownership
        slot = await self.repository.get(slot_id)
        if slot.seller_id == character.id:
            logger.warning(
                f"Unauthorized slot purchase attempt - Slot ID: {slot_id}, "
                f"Character ID: {character.id}"
            )
            raise PermissionDeniedError()

        # Получаем продавца до списания средств у покупателя: персонаж мог быть
        # удалён внутренним сервисным endpoint'ом, хотя основной нельзя отвязать.
        seller = await self.character_service.get_character_by_id(slot.seller_id)

        # Define variables for response
        currency_used = None
        amount_paid = Decimal("0.00")
        currency_received = None
        amount_received = Decimal("0.00")

        # Validate character has enough funds
        if slot.buy_for == Currency.GOLD:
            if character.gold < slot.gold:
                logger.warning(
                    f"Insufficient gold for slot purchase - Character: {character.id}, "
                    f"Required: {slot.gold}, Available: {character.gold}"
                )
                raise InsufficientFundsError(
                    detail="Not enough gold to buy slot",
                    required_amount=slot.gold,
                    current_amount=character.gold,
                    currency="gold"
                )
            else:
                buyer_gold = (character.gold - slot.gold).quantize(Decimal('0.01'))
                buyer_ducats = (character.ducats + slot.ducats).quantize(Decimal('0.01'))

                await self.character_update_service.update_character(
                    character.id,
                    CharacterUpdateSchema(
                        gold=buyer_gold,
                        ducats=buyer_ducats,
                        **character.model_dump(exclude={"gold", "ducats"})
                    )
                )
                await self.character_update_service.update_character(
                    seller.id,
                    CharacterUpdateSchema(
                        gold=(seller.gold + slot.gold).quantize(Decimal('0.01')),
                        ducats=seller.ducats,
                        **seller.model_dump(exclude={"gold", "ducats"})
                    )
                )

                currency_used = Currency.GOLD
                amount_paid = slot.gold
                currency_received = Currency.DUCATS
                amount_received = slot.ducats

        elif slot.buy_for == Currency.DUCATS:
            if character.ducats < slot.ducats:
                logger.warning(
                    f"Insufficient ducats for slot purchase - Character: {character.id}, "
                    f"Required: {slot.ducats}, Available: {character.ducats}"
                )
                raise InsufficientFundsError(
                    detail="Not enough ducats to buy slot",
                    required_amount=slot.ducats,
                    current_amount=character.ducats,
                    currency="ducats"
                )
            else:
                buyer_ducats = (character.ducats - slot.ducats).quantize(Decimal('0.01'))
                buyer_gold = (character.gold + slot.gold).quantize(Decimal('0.01'))

                await self.character_update_service.update_character(
                    character.id,
                    CharacterUpdateSchema(
                        gold=buyer_gold,
                        ducats=buyer_ducats,
                        **character.model_dump(exclude={"gold", "ducats"})
                    )
                )
                await self.character_update_service.update_character(
                    seller.id,
                    CharacterUpdateSchema(
                        gold=seller.gold,
                        ducats=(seller.ducats + slot.ducats).quantize(Decimal('0.01')),
                        **seller.model_dump(exclude={"gold", "ducats"})
                    )
                )

                currency_used = Currency.DUCATS
                amount_paid = slot.ducats
                currency_received = Currency.GOLD
                amount_received = slot.gold

        # Delete the slot after purchase
        await self.repository.delete(slot_id)
        
        logger.info(f"Slot purchase completed - Slot ID: {slot_id}, Character ID: {character.id}")

        return BuySlotResponse(
            success=True,
            slot_id=slot_id,
            buyer_id=character.id,
            currency_used=currency_used,
            amount_paid=amount_paid,
            currency_received=currency_received,
            amount_received=amount_received
        )

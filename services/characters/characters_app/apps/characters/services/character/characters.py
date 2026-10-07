import uuid
import logging
from typing import Protocol, Sequence
from typing_extensions import Self
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import exp
from shared.schemas.chat import ChatSettingsDefaultCreateSchema
from shared.schemas.characters import (
    CharacterReadSchema, CharacterSimpleReadSchema, 
    CharacterCreateSchema, CharacterSimpleListReadSchema,
    CharacterUpdateSchema, CharacterOnlineStatus,
)
from shared.enums import Race
from shared.exceptions import CharacterIsNotOnlineError
from .....core.utils.exceptions import ModelAlreadyExistsError, ModelNotFoundException, PermissionDeniedError
from ...models import Character
from ...repositories.character.characters import CharacterRepositoryProtocol
from ...adapters.files import FileServiceClientProtocol
from ...adapters.notebook import CreateNotebookAdapterProtocol
from ...adapters.panels import CreateItemsAdapterProtocol
from ...adapters.chats import ChatSettingsServiceClientProtocol
from ...adapters.category import CategoryServiceClientProtocol
from ..settings.global_settings import GlobalCharacterSettingsServiceProtocol
from ..settings.experience_settings import GlobalCharacterExperienceSettingsServiceProtocol
from ..settings.race_settings import RaceSettingsServiceProtocol
from ..settings.user_character_settings import UserCharacterSettingsServiceProtocol
from ..attachment.character_attachment_service import CharacterAttachmentSettingsServiceProtocol
from ..referrals.referral_link import ReferralLinkServiceProtocol
from ..info.characters_info import CharacterInfoServiceProtocol
from ..skills.character_ability_skills import CharacterAbilitySkillsServiceProtocol
from ..skills.applied_character_history import AppliedCharacterHistoryServiceProtocol
from ..skills.character_distributions import CharacterDistributionsServiceProtocol
from ....rest.services.house_guest_service import HouseGuestServiceProtocol
from ...events.publisher import RedisPublisherProtocol
from ....stats.services.publisher.stats_publisher import StatsPublisher
from ...schemas import (
    CharacterCreateDBSchema,
    CharacterUpdateDBSchema,
    GlobalCharacterSettingsReadSchema,
    RaceSettingsReadSchema,
    UserCharacterSettingsCreateSchema,
    CharacterCreationStatus,
    ReferralLinkCreateSchema,
    StatusSchema,
    CharacterFullInfoSchema,
    CharacterAbilitySkillsCreateSchema,
    CharacterAbilitySkillsUpdateDBSchema,
    AppliedCharacterHistoryCreateSchema,
    AppliedCharacterHistoryUpdateSchema,
    ChangeSkillsRequest, ChangeSkillsResponse,
    CharacterDistributionsUpdateSchema
)
from ...enums import CharacterSkillType
from ...exceptions import CharacterLimitExceededError, InsufficientFundsError, CannotDetachOnlineCharacterError, MaxSkillsExceededError, InsufficientFundsError

logger = logging.getLogger(__name__)

class CharacterCreateCheckerProtocol(Protocol):
    async def check_on_limit_characters(self: Self, user_id: uuid.UUID) -> CharacterCreationStatus:
        ...


class CharacterCreateChecker(CharacterCreateCheckerProtocol):
    def __init__(self: Self,
                 repository: CharacterRepositoryProtocol,
                 user_character_settings_service: UserCharacterSettingsServiceProtocol,
                 global_settings_service: GlobalCharacterSettingsServiceProtocol):
        self.repository = repository
        self.user_character_settings_service = user_character_settings_service
        self.global_settings_service = global_settings_service

    async def check_on_limit_characters(self: Self, user_id: uuid.UUID, default_max_characters: int = None) -> CharacterCreationStatus:
        count_characters = await self.repository.count_by_user_id(user_id)
        character_settings = await self.user_character_settings_service.get_by_user_id_or_none(user_id)
        max_characters = character_settings.max_characters if character_settings else None
        if not max_characters:
            if default_max_characters:
                max_characters = default_max_characters
            else:
                global_settings = (await self.global_settings_service.get_all())[0]
                max_characters = global_settings.max_characters_on_user

        can_create = count_characters < max_characters
        return CharacterCreationStatus(
            can_create=can_create,
            current_characters=count_characters,
            max_characters=max_characters
        )

class CharacterServiceProtocol(Protocol):
    async def get(self: Self, id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def create_default(self: Self, data: CharacterCreateSchema) -> CharacterReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: CharacterUpdateDBSchema) -> CharacterReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID) -> None:
        ...

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        ...

    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        ...

    async def get_simple(self: Self, id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...

    async def get_simple_by_ids(self: Self, ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        ...

    async def get_simple_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...

    async def get_simple_main_by_user_ids(self: Self, user_ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        ...

    async def add_stats_by_ability_skills(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        ...

    async def update_stats_by_ability_skills(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        ...

    async def calculate_change_skills_cost(self: Self, character_id: uuid.UUID, data: ChangeSkillsRequest) -> ChangeSkillsResponse:
        ...

class CharacterService(CharacterServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol,
                 global_settings_service: GlobalCharacterSettingsServiceProtocol,
                 race_settings_service: RaceSettingsServiceProtocol,
                 file_client: FileServiceClientProtocol,
                 user_character_settings_service: UserCharacterSettingsServiceProtocol,
                 character_checker: CharacterCreateChecker,
                 referral_link_service: ReferralLinkServiceProtocol,
                 notebook_adapter: CreateNotebookAdapterProtocol,
                 items_adapter: CreateItemsAdapterProtocol,
                 chat_settings_service: ChatSettingsServiceClientProtocol,
                 characters_info: CharacterInfoServiceProtocol,
                 ability_skills_service: CharacterAbilitySkillsServiceProtocol,
                 applied_character_history_service: AppliedCharacterHistoryServiceProtocol,
                 character_distributions_service: CharacterDistributionsServiceProtocol,
                 experience_settings_service: GlobalCharacterExperienceSettingsServiceProtocol
                 ):
        self.repository = repository
        self.global_settings_service = global_settings_service
        self.race_settings_service = race_settings_service
        self.file_client = file_client
        self.user_character_settings_service = user_character_settings_service
        self.character_checker = character_checker
        self.referral_link_service = referral_link_service
        self.notebook_adapter = notebook_adapter
        self.items_adapter = items_adapter
        self.chat_settings_service = chat_settings_service
        self.characters_info = characters_info
        self.ability_skills_service = ability_skills_service
        self.applied_character_history_service = applied_character_history_service
        self.character_distributions_service = character_distributions_service
        self.experience_settings_service = experience_settings_service

    async def get(self: Self, id: uuid.UUID) -> CharacterReadSchema:
        return await self.repository.get(id)

    async def get_simple_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.repository.get_simple_by_user_id(user_id)

    async def create_default(self: Self, data: CharacterCreateSchema) -> CharacterReadSchema:
        created_character = None
        try:
            # === Проверки и логика до создания ===
            exist_character = await self.repository.get_any_by_name_or_none(data.name)
            print("EXIST CHARACTER:", exist_character)
            if exist_character:
                raise ModelAlreadyExistsError(Character, "name", data.name)

            global_settings = (await self.global_settings_service.get_all())[0]
            creation_status = await self.character_checker.check_on_limit_characters(
                data.user_id, global_settings.max_characters_on_user
            )

            if not creation_status.can_create:
                raise CharacterLimitExceededError(creation_status.max_characters)

            is_main = creation_status.current_characters == 0

            race_settings = await self.race_settings_service.get_by_race(data.race)
            photo_id = await self._get_photo_id(data.race, data.is_male)

            character_data = self._build_character_create_schema(
                data,
                global_settings,
                race_settings,
                photo_id,
                is_main
            )

            modified_character, total_available_skills, total_weapon_skills = await self._modify_character_by_level(character_data)

            created_character = await self.repository.create(modified_character)

            character_ability_skills_data = CharacterAbilitySkillsCreateSchema(
                character_id=created_character.id,
                count_stats=total_available_skills,
                count_mastership=total_weapon_skills
            )

            await self.ability_skills_service.create(character_ability_skills_data)

            applied_character_history_data = AppliedCharacterHistoryCreateSchema(
                character_id=created_character.id
            )

            await self.applied_character_history_service.create(applied_character_history_data)

            # === Создание зависимостей ===
            if is_main:
                await self.user_character_settings_service.create_user_character_settings(
                    UserCharacterSettingsCreateSchema(
                        user_id=data.user_id,
                        max_characters=global_settings.max_characters_on_user
                    )
                )
                referral_link = ReferralLinkCreateSchema(
                    referrer_id=created_character.user_id,
                    referral_code=created_character.name
                )
                await self.referral_link_service.create_referral_link(referral_link)
                if data.referral_code:
                    is_created = await self.referral_link_service.add_new_referral(
                        created_character.user_id, data.referral_code
                    )
                    if not is_created:
                        logger.warning(f"Referral link with code {data.referral_code} not found for user {created_character.user_id}.")
                    else:
                        logger.info(f"Referral link with code {data.referral_code} successfully created for user {created_character.user_id}.")

            await self.notebook_adapter.create(created_character.id)
            await self.items_adapter.create(created_character.id)
            await self.characters_info.create_default(created_character.id)
            await self.chat_settings_service.create_default(
                data=ChatSettingsDefaultCreateSchema(character_id=created_character.id,
                                                     character_name=created_character.name,
                                                     is_main=created_character.is_main)
            )
            return created_character

        except Exception as e:
            logger.error(f"Error during character creation: {e}")

            # Если character был создан — удаляем его
            if created_character:
                try:
                    await self.repository.delete(created_character.id)
                    logger.info(f"Character {created_character.id} deleted due to error during creation.")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback character creation: {rollback_error}")

            raise  # Перебрасываем оригинальную ошибку

    async def add_stats_by_ability_skills(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        ability_skills = await self.ability_skills_service.get_by_character_id(character_id)
        sum_skills_added, sum_mastership_added = data.summarize()
        if sum_skills_added > ability_skills.count_stats:
            raise MaxSkillsExceededError(requested_skills=sum_skills_added, max_allowed_skills=ability_skills.count_stats)
        if sum_mastership_added > ability_skills.count_mastership:
            raise MaxSkillsExceededError(requested_skills=sum_mastership_added, max_allowed_skills=ability_skills.count_mastership)

        character = await self.repository.get(character_id)

        character.power += data.count_applied_power
        character.agility += data.count_applied_agility
        character.lucky += data.count_applied_lucky
        character.endurance += data.count_applied_endurance
        character.health = character.endurance * 6
        character.max_health = character.endurance * 6
        character.max_weight = character.endurance * 55
        character.intelligence += data.count_applied_intelligence
        character.mana = character.intelligence * 6
        character.max_mana = character.intelligence * 6
        character.mastership_sword += data.count_applied_mastership_sword
        character.mastership_axe += data.count_applied_mastership_axe
        character.mastership_hammer += data.count_applied_mastership_hammer
        
        update_data = CharacterUpdateDBSchema(**character.model_dump())
        updated_character = await self.repository.update(update_data)

        change_ability_skills = CharacterAbilitySkillsUpdateDBSchema(
            id=ability_skills.id,
            character_id=character_id,
            count_stats=ability_skills.count_stats - sum_skills_added,
            count_mastership=ability_skills.count_mastership - sum_mastership_added
        )

        await self.ability_skills_service.update(change_ability_skills)

        old_applied_stats = await self.applied_character_history_service.get_by_character_id(character_id)

        change_applied_history = AppliedCharacterHistoryUpdateSchema(
            character_id=character_id,
            count_applied_power=old_applied_stats.count_applied_power + data.count_applied_power,
            count_applied_agility=old_applied_stats.count_applied_agility + data.count_applied_agility,
            count_applied_lucky=old_applied_stats.count_applied_lucky + data.count_applied_lucky,
            count_applied_endurance=old_applied_stats.count_applied_endurance + data.count_applied_endurance,
            count_applied_intelligence=old_applied_stats.count_applied_intelligence + data.count_applied_intelligence,
            count_applied_mastership_sword=old_applied_stats.count_applied_mastership_sword + data.count_applied_mastership_sword,
            count_applied_mastership_axe=old_applied_stats.count_applied_mastership_axe + data.count_applied_mastership_axe,
            count_applied_mastership_hammer=old_applied_stats.count_applied_mastership_hammer + data.count_applied_mastership_hammer
        )

        await self.applied_character_history_service.update_by_character_id(character_id, change_applied_history)

        return updated_character
    
    async def update_stats_by_ability_skills(self: Self, character_id: uuid.UUID, data: AppliedCharacterHistoryCreateSchema) -> CharacterReadSchema:
        applied_skills = await self.applied_character_history_service.get_by_character_id(character_id)
        sum_skills_added, sum_mastership_added = data.summarize()
        sum_skills_applied, sum_mastership_applied = applied_skills.summarize()

        if sum_skills_added != sum_skills_applied and sum_mastership_added != sum_mastership_applied:
            raise MaxSkillsExceededError(
                requested_skills=sum_skills_added,            
                max_allowed_skills=sum_skills_applied,         
            )
        
        character = await self.repository.get(character_id)
        info_skills, info_mastership = None, None

        sum_ducats = Decimal("0")

        update_applied_history = AppliedCharacterHistoryUpdateSchema(
            **applied_skills.model_dump(exclude={'id'})
        )

        if sum_skills_added == sum_skills_applied:

            difference_power = data.count_applied_power - applied_skills.count_applied_power
            difference_agility = data.count_applied_agility - applied_skills.count_applied_agility
            difference_lucky = data.count_applied_lucky - applied_skills.count_applied_lucky
            difference_endurance = data.count_applied_endurance - applied_skills.count_applied_endurance
            difference_intelligence = data.count_applied_intelligence - applied_skills.count_applied_intelligence

            number_of_distributions_skills = int(sum([
                abs(difference_power),
                abs(difference_agility),
                abs(difference_lucky),
                abs(difference_endurance),
                abs(difference_intelligence)
            ]) / 2)

            if number_of_distributions_skills:
                info_skills = await self.character_distributions_service.get_by_character_id_and_skill_type(character_id, CharacterSkillType.STANDARD)
                
                info_skills.count_distributions += number_of_distributions_skills
                ducats = self._calculate_n_step(CharacterSkillType.STANDARD.coefficient, character.level, number_of_distributions_skills) 
                info_skills.price += ducats
                sum_ducats += Decimal(str(info_skills.price))

                character.power += difference_power
                character.agility += difference_agility
                character.lucky += difference_lucky
                character.endurance += difference_endurance
                character.health = character.endurance * 6
                character.max_health = character.endurance * 6
                character.max_weight = character.endurance * 55
                character.intelligence += difference_intelligence
                character.mana = character.intelligence * 6
                character.max_mana = character.intelligence * 6

                update_applied_history.count_applied_power = data.count_applied_power
                update_applied_history.count_applied_agility = data.count_applied_agility
                update_applied_history.count_applied_lucky = data.count_applied_lucky
                update_applied_history.count_applied_endurance = data.count_applied_endurance
                update_applied_history.count_applied_intelligence = data.count_applied_intelligence

        if sum_mastership_added == sum_mastership_applied:

            difference_mastership_sword = data.count_applied_mastership_sword - applied_skills.count_applied_mastership_sword
            difference_mastership_axe = data.count_applied_mastership_axe - applied_skills.count_applied_mastership_axe
            difference_mastership_hammer = data.count_applied_mastership_hammer - applied_skills.count_applied_mastership_hammer
        

            number_of_distributions_mastership = int(sum([
                abs(difference_mastership_sword),
                abs(difference_mastership_axe),
                abs(difference_mastership_hammer)
            ]) / 2)

            if number_of_distributions_mastership:
                info_mastership = await self.character_distributions_service.get_by_character_id_and_skill_type(character_id, CharacterSkillType.MASTERSHIP)

                info_mastership.count_distributions += number_of_distributions_mastership
                ducats = self._calculate_n_step(CharacterSkillType.MASTERSHIP.coefficient, character.level, number_of_distributions_mastership) 
                info_mastership.price += ducats
                sum_ducats += Decimal(str(info_mastership.price))

                character.mastership_sword += difference_mastership_sword
                character.mastership_axe += difference_mastership_axe
                character.mastership_hammer += difference_mastership_hammer
                update_applied_history.count_applied_mastership_sword = data.count_applied_mastership_sword
                update_applied_history.count_applied_mastership_axe = data.count_applied_mastership_axe
                update_applied_history.count_applied_mastership_hammer = data.count_applied_mastership_hammer

        if sum_ducats == 0:
            return character
        
        if character.ducats < Decimal(str(sum_ducats)):
            raise InsufficientFundsError(
                detail="Cannot afford to update skills",
                required_amount=sum_ducats,
                current_amount=character.ducats
            )

        character.ducats = (character.ducats - Decimal(str(sum_ducats))).quantize(Decimal('0.01'))

        character = await self.repository.update(CharacterUpdateDBSchema(**character.model_dump()))

        await self.applied_character_history_service.update_by_character_id(
            character_id,
            update_applied_history
        )

        if info_skills:
            await self.character_distributions_service.update(
                info_skills.id,
                CharacterDistributionsUpdateSchema(
                    character_id=character_id,
                    skill_type=CharacterSkillType.STANDARD,
                    count_distributions=info_skills.count_distributions,
                    price=info_skills.price
                )
            )

        if info_mastership:
            await self.character_distributions_service.update(
                info_mastership.id,
                CharacterDistributionsUpdateSchema(
                    character_id=character_id,
                    skill_type=CharacterSkillType.MASTERSHIP,
                    count_distributions=info_mastership.count_distributions,
                    price=info_mastership.price
                )
            )

        return character
    
    async def calculate_change_skills_cost(self: Self, character_id: uuid.UUID, data: ChangeSkillsRequest) -> ChangeSkillsResponse:
        character = await self.repository.get(character_id)
        base_total_cost = self._calculate_n_step(data.skill_type.coefficient, character.level, data.step)
        info = await self.character_distributions_service.get_by_character_id_and_skill_type(character_id, data.skill_type)
        final_total_cost = round(base_total_cost + info.price, 2)
        return ChangeSkillsResponse(
            total_cost=final_total_cost,
            skill_type=data.skill_type,
            step=data.step
        )

    def _calculate_n_step(self: Self, coef: float, level: int, n: int) -> int:
        if n == 0:
            return 0
        step_n = 0
        for i in range(n):
            step = coef*exp(0.0986*i)*level
            step_n += step
        return step_n

    async def _modify_character_by_level(self: Self, character_data: CharacterCreateDBSchema) -> tuple[CharacterCreateDBSchema, int]:
        level = character_data.level
        experience = character_data.experience

        available_stats = await self.experience_settings_service.find_all_by_level_and_max_experience(level, experience)

        total_intelligence = sum(stat.intelligence for stat in available_stats)
        total_endurance = sum(stat.endurance for stat in available_stats)
        total_race_parameter = sum(stat.race_parameter for stat in available_stats)
        total_available_skills = sum(stat.skills for stat in available_stats)
        total_weapon_skills = sum(stat.weapon_skill for stat in available_stats)
        total_available_ducats = sum(stat.ducats for stat in available_stats)

        character_data.intelligence += total_intelligence
        character_data.endurance += total_endurance
        character_data.health = character_data.endurance * 6
        character_data.max_health = character_data.endurance * 6
        character_data.mana = character_data.intelligence * 6
        character_data.max_mana = character_data.intelligence * 6
        character_data.max_weight = character_data.endurance * 55
        character_data.ducats += total_available_ducats

        return self._modify_character_race_skill(character_data, total_race_parameter), total_available_skills, total_weapon_skills
    
    def _modify_character_race_skill(self: Self, character_data: CharacterCreateDBSchema, race_parameter: int) -> CharacterCreateDBSchema:
        match character_data.race:
            case Race.ORC:
                character_data.power += race_parameter
            case Race.ELF:
                character_data.agility += race_parameter
            case Race.HUMAN:
                character_data.lucky += race_parameter
        return character_data

           
    async def update(self: Self, id: uuid.UUID, data: CharacterUpdateDBSchema) -> CharacterReadSchema:
        db_update = CharacterUpdateDBSchema(id=id,
                                            **data.model_dump()) 
        return await self.repository.update(db_update)

    async def delete(self: Self, id: uuid.UUID) -> None:
        await self.repository.delete(id)

    async def get_all_by_user(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        return await self.repository.get_all_by_user(user_id)

    async def get_by_name(self: Self, name: str) -> CharacterSimpleReadSchema:
        return await self.repository.get_by_name(name)
    
    async def get_simple(self: Self, id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.repository.get_simple(id)
    
    async def get_simple_by_ids(self: Self, ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        characters = await self.repository.get_simple_by_ids(ids)
        return CharacterSimpleListReadSchema(characters=characters)
    
    async def get_simple_main_by_user_ids(self: Self, user_ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        characters = await self.repository.get_simple_main_by_user_ids(user_ids)
        return CharacterSimpleListReadSchema(characters=characters)

    def _build_character_create_schema(self: Self, data: CharacterCreateSchema,
                                       global_settings: GlobalCharacterSettingsReadSchema,
                                       race_settings: RaceSettingsReadSchema,
                                       photo_id: uuid.UUID,
                                       is_main: bool = False) -> CharacterCreateDBSchema:
        return CharacterCreateDBSchema(
            name=data.name,
            user_id=data.user_id,
            race=data.race,
            is_male=data.is_male,
            level=global_settings.default_level,
            experience=global_settings.default_experience,
            health=global_settings.default_health,
            max_health=global_settings.default_max_health,
            endurance=global_settings.default_endurance,
            tiredness=global_settings.default_tiredness,
            max_tiredness=global_settings.default_max_tiredness,
            mana=global_settings.default_mana,
            max_mana=global_settings.default_max_mana,
            intelligence=global_settings.default_intelligence,
            weight=global_settings.default_weight,
            max_weight=global_settings.default_max_weight,
            gold=global_settings.default_gold,
            ducats=global_settings.default_ducats,
            power=race_settings.base_power,
            agility=race_settings.base_agility,
            lucky=race_settings.base_lucky,
            is_main=is_main,
            photo_id=photo_id,
            location_slug="1.17.station"
        )
    
    async def _get_photo_id(self: Self, race: Race, is_male: bool) -> uuid.UUID:
        gender = "male" if is_male else "female"
        template_name = f"{race.value}_{gender}_character"
        photo = await self.file_client.get_by_template(template_name)
        return photo.id


class CharacterAttachmentServiceProtocol(Protocol):
    async def detach(self: Self, user_id: uuid.UUID, detach_character_id: uuid.UUID) -> bool:
        ...

    async def has_detached_characters(self: Self, user_id: uuid.UUID) -> bool:
        ...

    async def get_detached_characters(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        ...

    async def attach(self: Self, user_id: uuid.UUID, attach_character_id: uuid.UUID) -> bool:
        """Method to attach a character back to the user."""
        ...

class CharacterAttachmentService(CharacterAttachmentServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol,
                 user_character_settings_service: UserCharacterSettingsServiceProtocol,
                 character_attachment_settings_service: CharacterAttachmentSettingsServiceProtocol,
                 period_deletion_days: int = 30
                 ):
        self.repository = repository
        self.user_character_settings_service = user_character_settings_service
        self.character_attachment_settings_service = character_attachment_settings_service
        self.period_deletion_days = period_deletion_days

    async def detach(self: Self, user_id: uuid.UUID, detach_character_id: uuid.UUID) -> bool:
        character = await self.repository.get(detach_character_id)
        if (not character.is_active) or character.user_id != user_id:
            raise ModelNotFoundException(Character, detach_character_id)
        
        if character.is_online:
            raise CannotDetachOnlineCharacterError(character_id=character.id, character_name=character.name)
        
        main_character = await self.repository.get_main_by_user_id(user_id)
        if main_character.id == detach_character_id:
            raise PermissionDeniedError("Cannot detach the main character")
        
        calculator = (await self.character_attachment_settings_service.get_all())[0]

        detach_cost = calculator.calculate_detach_cost(character.level)

        if main_character.ducats < detach_cost:
            raise InsufficientFundsError(
                detail="Cannot afford detach cost",
                required_amount=detach_cost,
                current_amount=main_character.ducats
            )
        
        changed_ducats = (main_character.ducats - Decimal(str(detach_cost))).quantize(Decimal('0.01'))
        transfer_gold = character.gold
        gold_for_main = (main_character.gold + transfer_gold).quantize(Decimal('0.01')) 
        await self.repository.update(
            CharacterUpdateDBSchema(
                ducats=changed_ducats,
                gold=gold_for_main,
                **main_character.model_dump(exclude={"ducats", "gold", "updated_at"})
            )
        )

        await self.repository.update(
            CharacterUpdateDBSchema(
                gold=Decimal("0"),
                is_active=False,
                deactivated_at=datetime.now(timezone.utc),
                scheduled_deletion_at=datetime.now(timezone.utc) + timedelta(days=self.period_deletion_days),
                **character.model_dump(exclude={"is_active", "gold", "deactivated_at", "scheduled_deletion_at", "updated_at"})
            )
        )

        return True
    
    async def has_detached_characters(self: Self, user_id: uuid.UUID) -> bool:
        return await self.repository.has_detached_characters(user_id)
    
    async def get_detached_characters(self: Self, user_id: uuid.UUID) -> list[CharacterReadSchema]:
        return await self.repository.get_detached_characters(user_id)

    async def attach(self: Self, user_id: uuid.UUID, attach_character_id: uuid.UUID) -> bool:
        """Method to attach a character back to the user."""
        character = await self.repository.get(attach_character_id)
        if character.is_active or character.user_id != user_id:
            raise ModelNotFoundException(Character, attach_character_id)
        
        # Check if the character is within the deletion period
        if character.scheduled_deletion_at < datetime.now(timezone.utc):
            raise ModelNotFoundException(Character, attach_character_id)
        
        main_character = await self.repository.get_main_by_user_id(user_id)
        if main_character.id == attach_character_id:
            raise PermissionDeniedError("Cannot attach the main character")

        count_characters = await self.repository.count_by_user_id(user_id)
        character_settings = await self.user_character_settings_service.get_by_user_id(user_id)
        if count_characters >= character_settings.max_characters:
            raise CharacterLimitExceededError(character_settings.max_characters)
        
        calculator = (await self.character_attachment_settings_service.get_all())[0]
        attach_cost = calculator.calculate_attach_cost(character.level)

        if main_character.gold < attach_cost:
            raise InsufficientFundsError(
                detail="Cannot afford attach cost",
                required_amount=attach_cost,
                current_amount=main_character.gold,
                currency="gold"
            )
        changed_gold = main_character.gold - attach_cost
        await self.repository.update(
            CharacterUpdateDBSchema(
                gold=changed_gold,
                **main_character.model_dump(exclude={"gold", "updated_at"})
            )
        )
        # Reactivate the character
        await self.repository.update(
            CharacterUpdateDBSchema(
                is_active=True,
                deactivated_at=None,
                scheduled_deletion_at=None,
                **character.model_dump(exclude={"is_active", "deactivated_at", "scheduled_deletion_at", "updated_at"})
            )
        )
        
        return True
    

class CharacterCleanupServiceProtocol(Protocol):
    async def delete_all_detached_characters(self: Self) -> bool:
        ...

class CharacterCleanupService(CharacterCleanupServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def delete_all_detached_characters(self: Self) -> bool:
        return await self.repository.delete_all_detached_characters()
    
class GetMainCharacterByUserIdProtocol(Protocol):
    async def get_main_character_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        ...

    async def get_character_by_id(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        ...

class GetMainCharacterByUserIdService(GetMainCharacterByUserIdProtocol):

    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def get_main_character_by_user_id(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        return await self.repository.get_main_by_user_id(user_id)
    
    async def get_character_by_id(self: Self, character_id: uuid.UUID) -> CharacterReadSchema:
        return await self.repository.get(character_id)

class UpdateCharacterProtocol(Protocol):
    async def update_character(self: Self, character_id: uuid.UUID, data: CharacterUpdateSchema) -> CharacterReadSchema:
        ...

class UpdateCharacterService(UpdateCharacterProtocol):

    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def update_character(self: Self, character_id: uuid.UUID, data: CharacterUpdateSchema) -> CharacterReadSchema:
        db_update = CharacterUpdateDBSchema(id=character_id,
                                            **data.model_dump()) 
        return await self.repository.update(db_update)
    
class UpdateCharacterStatusServiceProtocol(Protocol):
    async def update_character_status(self: Self, character_id: uuid.UUID, status: StatusSchema) -> CharacterReadSchema:
        ...

    async def bulk_update_characters_to_offline(self: Self, character_ids: list[uuid.UUID]) -> int:
        ...

class UpdateCharacterStatusService(UpdateCharacterStatusServiceProtocol):

    def __init__(
        self: Self,
        repository: CharacterRepositoryProtocol,
        publisher: RedisPublisherProtocol | None = None,
        house_guest_service: HouseGuestServiceProtocol | None = None,
    ):
        self.repository = repository
        self.publisher = publisher
        self.house_guest_service = house_guest_service

    async def update_character_status(self: Self, character_id: uuid.UUID, status: StatusSchema) -> CharacterReadSchema:
        updated = await self.repository.update_character_status(character_id, status)

        # При уходе в оффлайн — выключаем из дома
        if not status.is_online and self.house_guest_service:
            try:
                offline_character = await self.repository.get(character_id)
                await self.house_guest_service.leave_on_offline(offline_character)
            except Exception as e:
                logger.error(f"Failed to leave house on offline for {character_id}: {e}")
        
        # Публикуем событие смены онлайн-статуса
        if self.publisher:
            try:
                from shared.schemas.characters import CharacterOnlineStatusChangedEvent
                from datetime import datetime, timezone
                # Читаем актуальные данные из БД
                character = await self.repository.get(character_id)
                
                event = CharacterOnlineStatusChangedEvent(
                    character_id=character_id,
                    is_online=status.is_online,
                    location_slug=character.location_slug,
                    current_room_id=character.current_room_id,
                    name=character.name,
                    level=character.level,
                    race=character.race.value if character.race else None,
                )
                event_data = {
                    "event_type": "online_status_changed",
                    "data": event.model_dump(mode='json'),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await self.publisher.publish("online_status_changed", event_data)
                logger.info(f"Published online_status_changed for character {character_id}: is_online={character.is_online}")
            except Exception as e:
                logger.error(f"Failed to publish online_status_changed: {e}")
        
        return updated

    async def bulk_update_characters_to_offline(self: Self, character_ids: list[uuid.UUID]) -> int:
        count = await self.repository.bulk_update_characters_to_offline(character_ids)
        
        # Публикуем событие offline для каждого персонажа
        if self.publisher and character_ids:
            try:
                from shared.schemas.characters import CharacterOnlineStatusChangedEvent
                from datetime import datetime, timezone
                
                # Получаем данные персонажей для события
                for character_id in character_ids:
                    try:
                        character = await self.repository.get(character_id)

                        # Выключаем из дома перед публикацией offline
                        if self.house_guest_service:
                            await self.house_guest_service.leave_on_offline(character)

                        event = CharacterOnlineStatusChangedEvent(
                            character_id=character_id,
                            is_online=False,
                            location_slug=character.location_slug,
                            current_room_id=character.current_room_id,
                            name=character.name,
                            level=character.level,
                            race=character.race.value if character.race else None,
                        )
                        event_data = {
                            "event_type": "online_status_changed",
                            "data": event.model_dump(mode='json'),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await self.publisher.publish("online_status_changed", event_data)
                    except Exception as e:
                        logger.warning(f"Failed to publish offline event for character {character_id}: {e}")
            except Exception as e:
                logger.error(f"Failed to publish bulk offline events: {e}")
        
        return count

class GetFullInfoCharacterServiceProtocol(Protocol):
    async def get_character_info(self: Self, character_id: uuid.UUID) -> CharacterFullInfoSchema:
        ...

    async def get_character_info_by_name(self: Self, name: str) -> CharacterFullInfoSchema:
        ...

class GetFullInfoCharacterService(GetFullInfoCharacterServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol,
                 characters_info: CharacterInfoServiceProtocol,
                 category_service: CategoryServiceClientProtocol):
        self.repository = repository
        self.characters_info = characters_info
        self.category_service = category_service

    async def get_character_info(self: Self, character_id: uuid.UUID) -> CharacterFullInfoSchema:
        character = await self.repository.get(character_id)
        character_info = await self.characters_info.get_by_character_id(character_id)
        categories_stats = await self.category_service.get_categories_stats(character.id)
        return CharacterFullInfoSchema(
            info=character,
            additional_info=character_info,
            categories_stats=categories_stats
        )
    
    async def get_character_info_by_name(self: Self, name: str) -> CharacterFullInfoSchema:
        character = await self.repository.get_full_by_name(name)
        character_info = await self.characters_info.get_by_character_id(character.id)
        categories_stats = await self.category_service.get_categories_stats(character.id)

        return CharacterFullInfoSchema(
            info=character,
            additional_info=character_info,
            categories_stats=categories_stats
        )
    

class GetIsOnlineCharacterServiceProtocol(Protocol):
    async def get_is_online(self: Self, id: uuid.UUID) -> CharacterOnlineStatus:
        ...

class GetIsOnlineCharacterService(GetIsOnlineCharacterServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def get_is_online(self: Self, id: uuid.UUID) -> CharacterOnlineStatus:
        is_online = await self.repository.is_online(id)
        return CharacterOnlineStatus(is_online=is_online)
    
class UpdateCharacterTirednessServiceProtocol(Protocol):
    async def update_tiredness(self: Self, character_id: uuid.UUID, tiredness: float) -> None:
        ...

class UpdateCharacterTirednessService(UpdateCharacterTirednessServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol, publisher: StatsPublisher | None = None):
        self.repository = repository
        self.publisher = publisher

    async def update_tiredness(self: Self, character_id: uuid.UUID, tiredness: float) -> None:
        await self.repository.update_tiredness(character_id, tiredness)

        # Публикуем через единый издатель: health/mana/tiredness из БД
        if self.publisher:
            try:
                await self.publisher.publish_regeneration(character_id)
            except Exception as e:
                logger.error(f"Failed to publish stats update for tiredness: {e}")


class UpdateCharacterDucatsServiceProtocol(Protocol):
    async def update_ducats(self: Self, character_id: uuid.UUID, ducats: Decimal) -> bool:
        ...

class UpdateCharacterDucatsService(UpdateCharacterDucatsServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def update_ducats(self: Self, character_id: uuid.UUID, ducats: Decimal) -> bool:
        return await self.repository.update_ducats(character_id, ducats)


class CharacterWeightBalanceServiceProtocol(Protocol):
    async def get_weight_balance(self: Self, character_id: uuid.UUID) -> dict:
        ...

class CharacterWeightBalanceService(CharacterWeightBalanceServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def get_weight_balance(self: Self, character_id: uuid.UUID) -> dict:
        return await self.repository.get_weight_balance(character_id)


class UpdateCharacterWeightServiceProtocol(Protocol):
    async def update_weight(self: Self, character_id: uuid.UUID, weight: float) -> bool:
        ...

class UpdateCharacterWeightService(UpdateCharacterWeightServiceProtocol):
    def __init__(self: Self, repository: CharacterRepositoryProtocol):
        self.repository = repository

    async def update_weight(self: Self, character_id: uuid.UUID, weight: float) -> bool:
        return await self.repository.update_weight(character_id, weight)
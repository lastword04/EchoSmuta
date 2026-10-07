import sqlalchemy as sa
from typing import Protocol
from typing_extensions import Self
from datetime import datetime, timezone
from ....core.use_cases import UseCaseProtocol
from ...characters.models import Character
from ...rest.models import RestRental, House
from ....settings import settings
from ..models import CharacterBuff
from ..services.publisher.stats_publisher import StatsPublisher


class PassiveRegenerationUseCaseProtocol(UseCaseProtocol[int]):
    async def __call__(self: Self) -> int: ...


class PassiveRegenerationUseCase(PassiveRegenerationUseCaseProtocol):
    def __init__(self: Self, publisher: StatsPublisher, session):
        self.publisher = publisher
        self.session = session 

    async def __call__(self: Self) -> int:
        """Обработать регенерацию всех онлайн персонажей"""

        def _jsonb_float_bonus(column, key: str):
            raw = column.op('->>')(key)
            return sa.func.coalesce(sa.cast(raw, sa.Float), 0.0)

        # Эффективные максимумы с учётом equipment_bonuses
        eff_max_health = Character.max_health + _jsonb_float_bonus(Character.equipment_bonuses, 'max_health_bonus')
        eff_max_mana = Character.max_mana + _jsonb_float_bonus(Character.equipment_bonuses, 'max_mana_bonus')
        eff_max_tiredness = Character.max_tiredness + _jsonb_float_bonus(Character.equipment_bonuses, 'max_tiredness_bonus')

        # Множители из настроек (гостиница)
        health_mult = settings.rest_health_multiplier
        tiredness_mult = settings.rest_tiredness_multiplier
        mana_mult = settings.rest_mana_multiplier

        # Подзапрос для активных аренд с состоянием "inside"
        active_rentals = (
            sa.select(RestRental.character_id)
            .where(
                RestRental.expires_at > datetime.now(timezone.utc)
            )
            .scalar_subquery()
        )

        # Подзапросы для множителей дома
        house_health_mult = (
            sa.select(
                sa.func.coalesce(
                    sa.cast(House.regen_multipliers.op('->>')('health'), sa.Float),
                    1.0
                )
            )
            .where(House.id == Character.current_house_id)
            .correlate(Character)
            .scalar_subquery()
        )

        house_mana_mult = (
            sa.select(
                sa.func.coalesce(
                    sa.cast(House.regen_multipliers.op('->>')('mana'), sa.Float),
                    1.0
                )
            )
            .where(House.id == Character.current_house_id)
            .correlate(Character)
            .scalar_subquery()
        )

        house_tiredness_mult = (
            sa.select(
                sa.func.coalesce(
                    sa.cast(House.regen_multipliers.op('->>')('tiredness'), sa.Float),
                    1.0
                )
            )
            .where(House.id == Character.current_house_id)
            .correlate(Character)
            .scalar_subquery()
        )

        # HP с учётом дома и гостиницы
        hp_stmt = (
            sa.update(Character)
            .where(
                Character.is_active == True,
                Character.is_banned == False,
                Character.health < eff_max_health
            )
            .values(
                health=sa.case(
                    # Дом имеет приоритет
                    (
                        Character.current_house_id.isnot(None),
                        sa.func.least(
                            Character.health + (eff_max_health / 540.0 * sa.func.coalesce(house_health_mult, 1.0)),
                            eff_max_health
                        )
                    ),
                    # Гостиница
                    (
                        sa.and_(
                            Character.rest_state == "inside",
                            Character.id.in_(active_rentals)
                        ),
                        sa.func.least(
                            Character.health + (eff_max_health / 540.0 * health_mult),
                            eff_max_health
                        )
                    ),
                    # Обычный реген
                    else_=sa.func.least(Character.health + (eff_max_health / 540.0), eff_max_health)
                )
            )
        )
        await self.session.execute(hp_stmt)

        # Mana с учётом дома и гостиницы
        mana_stmt = (
            sa.update(Character)
            .where(
                Character.is_active == True,
                Character.is_banned == False,
                Character.mana < eff_max_mana
            )
            .values(
                mana=sa.case(
                    # Дом имеет приоритет
                    (
                        Character.current_house_id.isnot(None),
                        sa.func.least(
                            Character.mana + (eff_max_mana / 1620.0 * sa.func.coalesce(house_mana_mult, 1.0)),
                            eff_max_mana
                        )
                    ),
                    # Гостиница
                    (
                        sa.and_(
                            Character.rest_state == "inside",
                            Character.id.in_(active_rentals)
                        ),
                        sa.func.least(
                            Character.mana + (eff_max_mana / 1620.0 * mana_mult),
                            eff_max_mana
                        )
                    ),
                    # Обычный реген
                    else_=sa.func.least(Character.mana + (eff_max_mana / 1620.0), eff_max_mana)
                )
            )
        )
        await self.session.execute(mana_stmt)

        # Усталость с учётом дома и гостиницы
        stamina_stmt = (
            sa.update(Character)
            .where(
                Character.is_active == True,
                Character.is_banned == False,
                Character.tiredness > 0
            )
            .values(
                tiredness=sa.case(
                    # Дом имеет приоритет
                    (
                        Character.current_house_id.isnot(None),
                        sa.func.greatest(
                            Character.tiredness - (eff_max_tiredness / 2160.0 * sa.func.coalesce(house_tiredness_mult, 1.0)),
                            0.0
                        )
                    ),
                    # Гостиница
                    (
                        sa.and_(
                            Character.rest_state == "inside",
                            Character.id.in_(active_rentals)
                        ),
                        sa.func.greatest(
                            Character.tiredness - (eff_max_tiredness / 2160.0 * tiredness_mult),
                            0.0
                        )
                    ),
                    # Обычный реген
                    else_=sa.func.greatest(Character.tiredness - (eff_max_tiredness / 2160.0), 0.0)
                )
            )
        )
        await self.session.execute(stamina_stmt)

        # Деактивация истёкших баффов
        deactivate_stmt = (
            sa.update(CharacterBuff)
            .where(
                CharacterBuff.is_active == True,
                CharacterBuff.expires_at != None,
                CharacterBuff.expires_at <= datetime.utcnow()
            )
            .values(is_active=False)
        )
        await self.session.execute(deactivate_stmt)

        await self.session.commit()

        # Получаем онлайн-персонажей и публикуем регенерацию
        result = await self.session.execute(
            sa.select(Character).where(
                Character.is_online == True,
                Character.is_active == True
            )
        )
        online_chars = list(result.scalars().all())

        for char in online_chars:
            await self.publisher.publish_regeneration(char.id)

        return len(online_chars)
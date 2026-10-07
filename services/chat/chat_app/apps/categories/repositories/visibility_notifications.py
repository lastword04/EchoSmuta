import uuid
from typing import Protocol
from typing_extensions import Self
import sqlalchemy as sa
from ..models import Category, CategoryCharacter
from ....core.db import AsyncSession

class CheckVisibilityNotificationsRepositoryProtocol(Protocol):
    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        ...

    async def get_notification_receivers_for_target(
        self: Self,
        owner_character_id: uuid.UUID
    ) -> list[uuid.UUID]:
        ...

class CheckVisibilityNotificationsRepository(CheckVisibilityNotificationsRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_visible_notifications(
        self: Self, 
        owner_character_id: uuid.UUID, 
        target_character_id: uuid.UUID
    ) -> bool:
        """
        Проверяет, можно ли отображать уведомления между двумя персонажами.
        """
        async with self.session as s:
            OwnerCategory = sa.orm.aliased(Category, name="owner_category")
            TargetCategory = sa.orm.aliased(Category, name="target_category")
            
            statement = (
                sa.select(1)
                .select_from(OwnerCategory)
                .join(
                    CategoryCharacter,
                    CategoryCharacter.category_id == OwnerCategory.id
                )
                .join(
                    TargetCategory,
                    sa.and_(
                        TargetCategory.name == OwnerCategory.name,
                        TargetCategory.owner_character_id == target_character_id
                    )
                )
                .where(
                    OwnerCategory.owner_character_id == owner_character_id,
                    OwnerCategory.name.in_(["Друзья", "Враги"]),
                    OwnerCategory.is_receive_notifications == True,
                    CategoryCharacter.character_id == target_character_id,
                    TargetCategory.is_send_notifications == True
                )
                .limit(1)
            )
            
            result = await s.execute(statement)
            return result.scalar() is not None
        
    async def get_notification_receivers_for_target(
        self: Self,
        target_character_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """
        Возвращает список owner_character_id, которые могут получать уведомления
        от target_character_id.
        target_character_id = персонаж, который отправляет (is_send_notifications=True)
        owner_character_id = персонажи, которые принимают (is_receive_notifications=True)
        """
        async with self.session as s:
            TargetCategory = sa.orm.aliased(Category, name="target_category")
            OwnerCategory = sa.orm.aliased(Category, name="owner_category")

            statement = (
                sa.select(OwnerCategory.owner_character_id.distinct())
                .select_from(TargetCategory)
                .join(
                    OwnerCategory,
                    sa.and_(
                        OwnerCategory.name == TargetCategory.name
                    )
                )
                .join(
                    CategoryCharacter,
                    sa.and_(
                        CategoryCharacter.category_id == OwnerCategory.id,
                        CategoryCharacter.character_id == TargetCategory.owner_character_id
                    )
                )
                .where(
                    TargetCategory.owner_character_id == target_character_id,
                    TargetCategory.name.in_(["Друзья", "Враги"]),
                    TargetCategory.is_send_notifications == True,
                    OwnerCategory.is_receive_notifications == True
                )
            )

            result = await s.execute(statement)
            return list(result.scalars().all())


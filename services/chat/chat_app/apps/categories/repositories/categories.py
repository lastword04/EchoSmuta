import uuid
import sqlalchemy as sa
from typing_extensions import Self
from shared.schemas.category import BaseCategoryStatsSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException
from ..models import Category, CategoryCharacter
from ..schemas import (
    CategoryCreateDBSchema, CategoryReadSchema, 
    CategoryUpdateSchema, CategoryWithCharacterCountSchema,
    CategoryUpdateCheckbox
)

class CategoryRepositoryProtocol(BaseRepositoryImpl[
    Category,
    CategoryReadSchema,
    CategoryCreateDBSchema,
    CategoryUpdateSchema
]):
    async def delete(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        ...

    async def get_all_by_character_id(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        ...

    async def get_all_by_character_id_with_character_count(self: Self, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        ...

    async def update_checkbox_fields(
        self: Self, 
        category_id: uuid.UUID, 
        character_id: uuid.UUID,
        update_data: CategoryUpdateCheckbox
    ) -> CategoryReadSchema:
        ...

    async def calculate_stats_base_category(self: Self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        ...

class CategoryRepository(CategoryRepositoryProtocol):
    async def delete(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> bool:
        async with self.session as s, s.begin():
            statement = (
                sa.delete(self.model_type)
                .where(self.model_type.id == category_id,
                       self.model_type.owner_character_id == character_id,
                       self.model_type.is_main == False)
            )
            await s.execute(statement)
            return True
        
    async def get_all_by_character_id(self: Self, character_id: uuid.UUID) -> list[CategoryReadSchema]:
        async with self.session as s:
            statement = (
                sa.select(self.model_type)
                .where(self.model_type.owner_character_id == character_id)
                .order_by(self.model_type.created_at.asc()) 
            )

            models = (await s.execute(statement)).scalars().all()

            return [self.read_schema_type.model_validate(model, from_attributes=True) for model in models]

    async def get_all_by_character_id_with_character_count(self: Self, character_id: uuid.UUID) -> list[CategoryWithCharacterCountSchema]:
        async with self.session as s:
            # Подзапрос для подсчета количества персонажей в каждой категории
            count_subquery = (
                sa.select(
                    CategoryCharacter.category_id,
                    sa.func.count(CategoryCharacter.character_id).label('characters_count')
                )
                .group_by(CategoryCharacter.category_id)
                .subquery()
            )
            
            statement = (
                sa.select(
                    self.model_type,
                    sa.func.coalesce(count_subquery.c.characters_count, 0).label('characters_count')
                )
                .select_from(
                    self.model_type.__table__.join(
                        count_subquery,
                        self.model_type.id == count_subquery.c.category_id,
                        isouter=True
                    )
                )
                .where(self.model_type.owner_character_id == character_id)
                .order_by(self.model_type.created_at.asc()) 
            )

            result = await s.execute(statement)
            rows = result.all()

            categories_with_counts = []
            for row in rows:
                # Объединяем данные модели и подсчитанное количество
                category_dict = row[0].__dict__.copy()
                category_dict['characters_count'] = row[1]
                categories_with_counts.append(
                    CategoryWithCharacterCountSchema.model_validate(category_dict, from_attributes=True)
                )

            return categories_with_counts
        
    async def update_checkbox_fields(
        self: Self, 
        category_id: uuid.UUID, 
        character_id: uuid.UUID,
        update_data: CategoryUpdateCheckbox
    ) -> CategoryReadSchema:
        async with self.session as s, s.begin():
            # Получаем категорию
            statement = (
                sa.select(self.model_type)
                .where(
                    self.model_type.id == category_id,
                    self.model_type.owner_character_id == character_id
                )
            )
            result = await s.execute(statement)
            category = result.scalar_one_or_none()
            
            if not category:
                raise ModelNotFoundException(self.model_type, category_id)
            
            # Если категория is_main, можно обновлять все поля
            if category.is_main:
                if update_data.is_send_notifications is not None:
                    category.is_send_notifications = update_data.is_send_notifications
                if update_data.is_receive_notifications is not None:
                    category.is_receive_notifications = update_data.is_receive_notifications
                category.is_block_send_mails = update_data.is_block_send_mails
            else:
                # Если категория не is_main, можно обновлять только is_block_send_mails
                category.is_block_send_mails = update_data.is_block_send_mails
            
            await s.flush()
            await s.refresh(category)
            
            return self.read_schema_type.model_validate(category, from_attributes=True)
        
    async def calculate_stats_base_category(self: Self, character_id: uuid.UUID) -> BaseCategoryStatsSchema:
        async with self.session as s:
            # Найдем ID категорий "Друзья" и "Враги" для данного character_id
            friends_category_alias = sa.orm.aliased(Category)
            enemies_category_alias = sa.orm.aliased(Category)

            # Подзапросы для получения ID категорий
            friends_category_subq = (
                sa.select(friends_category_alias.id)
                .where(
                    friends_category_alias.name == "Друзья", # или используйте константу
                    friends_category_alias.owner_character_id == character_id
                )
                .scalar_subquery()
            )

            enemies_category_subq = (
                sa.select(enemies_category_alias.id)
                .where(
                    enemies_category_alias.name == "Враги", # или используйте константу
                    enemies_category_alias.owner_character_id == character_id
                )
                .scalar_subquery()
            )

            # Подсчет количества персонажей в категории "Друзья"
            friends_count_stmt = (
                sa.select(sa.func.count(CategoryCharacter.character_id))
                .where(CategoryCharacter.category_id == friends_category_subq)
            )

            # Подсчет количества персонажей в категории "Враги"
            enemies_count_stmt = (
                sa.select(sa.func.count(CategoryCharacter.character_id))
                .where(CategoryCharacter.category_id == enemies_category_subq)
            )

            # Выполним оба запроса
            friends_result = await s.execute(friends_count_stmt)
            enemies_result = await s.execute(enemies_count_stmt)

            friends_count = friends_result.scalar() or 0
            enemies_count = enemies_result.scalar() or 0

            return BaseCategoryStatsSchema(
                friends_count=friends_count,
                enemies_count=enemies_count
            )
import uuid
import sqlalchemy as sa
from typing_extensions import Self
from sqlalchemy.orm import selectinload
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import ModelNotFoundException, ModelAlreadyExistsError
from ..exceptions import CategoryCharacterLimitExceededError
from ..models import Category, CategoryCharacter
from ..schemas import (
    CategoryCharacterCreateSchema, CategoryCharacterReadSchema, 
    CategoryCharacterUpdateSchema, CategoryWithCharacterIdsReadSchema
)


class CategoryCharacterRepositoryProtocol(BaseRepositoryImpl[
    CategoryCharacter,
    CategoryCharacterReadSchema,
    CategoryCharacterCreateSchema,
    CategoryCharacterUpdateSchema
]):
    async def add_character_to_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID) -> CategoryCharacterReadSchema:
        ...

    async def get_by_category_id(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> CategoryWithCharacterIdsReadSchema:
        ...

    async def delete_character_from_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID) -> bool:
        ...

class CategoryCharacterRepository(CategoryCharacterRepositoryProtocol):
    async def add_character_to_category(
    self: Self, 
    category_id: uuid.UUID, 
    character_id: uuid.UUID, 
    owner_character_id: uuid.UUID
) -> CategoryCharacterReadSchema:
        async with self.session as s, s.begin():
            # Получаем категорию и текущее количество персонажей за один запрос
            stmt = (
                sa.select(Category, sa.func.count(self.model_type.id).label('current_count'))
                .select_from(
                    Category.__table__.join(
                        self.model_type,
                        Category.id == self.model_type.category_id,
                        isouter=True
                    )
                )
                .where(
                    Category.id == category_id,
                    Category.owner_character_id == owner_character_id
                )
                .group_by(Category.id)
            )
            result = await s.execute(stmt)
            row = result.first()
            
            if not row:
                raise ModelNotFoundException(Category, category_id)
            
            category, current_count = row.Category, row.current_count
            
            # Проверяем лимит
            if current_count >= category.max_count_characters:
                raise CategoryCharacterLimitExceededError(
                    category_id=category_id,
                    max_characters=category.max_count_characters,
                )
            
            # Проверяем, не добавлен ли уже этот персонаж в целевую категорию
            exists_stmt = (
                sa.select(self.model_type)
                .where(
                    self.model_type.character_id == character_id,
                    self.model_type.category_id == category_id
                )
            )
            exists = await s.execute(exists_stmt)
            
            if exists.scalar_one_or_none():
                # Возвращаем существующую запись (хотя после удаления этого не должно быть)
                raise ModelAlreadyExistsError(
                    self.model_type, 
                    "character_id and category_id", 
                    f"{character_id} and {category_id}"
                )
            
            # Находим все категории, принадлежащие owner_character_id
            owner_categories_stmt = (
                sa.select(Category.id)
                .where(Category.owner_character_id == owner_character_id)
            )
            owner_categories_result = await s.execute(owner_categories_stmt)
            owner_category_ids = [row[0] for row in owner_categories_result.fetchall()]
            
            # Удаляем записи о character_id из всех категорий владельца, если они существуют
            if owner_category_ids:
                delete_stmt = (
                    sa.delete(self.model_type)
                    .where(
                        self.model_type.character_id == character_id,
                        self.model_type.category_id.in_(owner_category_ids)
                    )
                )
                await s.execute(delete_stmt)            
            
            # Создаем новую запись через insert
            insert_stmt = (
                sa.insert(self.model_type)
                .values(
                    character_id=character_id,
                    category_id=category_id
                )
                .returning(self.model_type)  # Возвращаем созданную запись
            )
            
            result = await s.execute(insert_stmt)
            created_category_character = result.scalar_one()
            
            return self.read_schema_type.model_validate(
                created_category_character, 
                from_attributes=True
            )
        
    async def get_by_category_id(self: Self, category_id: uuid.UUID, character_id: uuid.UUID) -> CategoryWithCharacterIdsReadSchema:
        async with self.session as s:
            # Найдём саму категорию
            category_stmt = (
                sa.select(Category.id, Category.name)
                .where(
                    Category.id == category_id,
                    Category.owner_character_id == character_id
                )
            )

            category_result = await s.execute(category_stmt)
            category_row = category_result.first()

            if not category_row:
                raise ModelNotFoundException(Category, category_id)

            # Теперь найдём связанные character_id
            cc_stmt = (
                sa.select(CategoryCharacter.character_id)
                .where(CategoryCharacter.category_id == category_id)
            )

            cc_result = await s.execute(cc_stmt)
            characters_ids = [row.character_id for row in cc_result.all()]

            return CategoryWithCharacterIdsReadSchema(
                id=category_row.id,
                name=category_row.name,
                characters_ids=characters_ids
            )
    
    async def delete_character_from_category(self: Self, category_id: uuid.UUID, character_id: uuid.UUID, owner_character_id: uuid.UUID) -> bool:
        async with self.session as s, s.begin():
            stmt = (
                sa.delete(self.model_type)
                .where(
                    self.model_type.category_id == category_id,
                    self.model_type.character_id == character_id,
                    self.model_type.category_id.in_(
                        sa.select(Category.id)
                        .where(Category.owner_character_id == owner_character_id)
                        .scalar_subquery()
                    )
                )
            )

            await s.execute(stmt)

            return True

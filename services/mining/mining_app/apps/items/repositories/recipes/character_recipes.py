from typing import Protocol, Self

import sqlalchemy as sa
from sqlalchemy.orm import contains_eager, joinedload

from .....core.db import AsyncSession
from ....resources.models import Resource
from ...models import CharacterRecipes, Item, ItemComponent, ItemPrice
from ...schemas import (
    CharacterRecipeReadSchema,
    ItemComponentWithResourceSchema,
    ItemReadSchema,
    ResourceItemWithComponentsReadSchema,
)


class CharacterRecipesRepositoryProtocol(Protocol):
    async def get_all_recipes(self: Self, location_slug: str, quantity: int) -> list[ResourceItemWithComponentsReadSchema]:
        ...
    
    async def get_character_recipes(self: Self, character_id) -> list[CharacterRecipeReadSchema]:
        ...
    
    async def get_recipe_price(self: Self, item_slug: str, quantity: int) -> float | None:
        ...
    
    async def create_character_recipe(self: Self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema:
        ...
    
    async def get_by_character_item_and_quantity(self: Self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema | None:
        ...
    
    async def get_for_character(self: Self, recipe_id, character_id) -> CharacterRecipeReadSchema | None:
        ...
    
    async def decrement_quantity_for_character(self: Self, recipe_id, character_id) -> bool:
        ...

    async def delete_by_character_item_and_quantity(self: Self, character_id, item_slug: str, quantity: int) -> bool:
        ...

class CharacterRecipesRepository(CharacterRecipesRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session
    
    async def get_all_recipes(self: Self, location_slug: str, quantity: int) -> list[ResourceItemWithComponentsReadSchema]:
        async with self.session as s:
            stmt = (
                sa.select(Item)
                .outerjoin(
                    ItemPrice,
                    (Item.slug == ItemPrice.item_slug) & (ItemPrice.quantity == quantity)
                )
                .where(Item.location_slug == location_slug)
                .options(contains_eager(Item.prices))
                .order_by(Item.name)
            )

            result = await s.scalars(stmt)
            items = [item for item in result.unique().all() if item.prices]

            if not items:
                return []

            # Одним запросом забираем компоненты ВСЕХ предметов + названия ресурсов
            slugs = [item.slug for item in items]
            components_stmt = (
                sa.select(ItemComponent, Resource.name.label("resource_name"))
                .join(Resource, ItemComponent.resource_slug == Resource.slug)
                .where(ItemComponent.item_slug.in_(slugs))
            )
            components_result = await s.execute(components_stmt)

            # Группируем компоненты по item_slug
            components_by_slug: dict[str, list[ItemComponentWithResourceSchema]] = {}
            for component, resource_name in components_result.all():
                components_by_slug.setdefault(component.item_slug, []).append(
                    ItemComponentWithResourceSchema(
                        id=component.id,
                        item_slug=component.item_slug,
                        resource_slug=component.resource_slug,
                        quantity=component.quantity,
                        resource_name=resource_name,
                    )
                )

            return [
                ResourceItemWithComponentsReadSchema(
                    **{k: v for k, v in item.__dict__.items() if not k.startswith("_")},
                    recipe_price=item.prices[0].price,
                    components=components_by_slug.get(item.slug, []),
                )
                for item in items
            ]
    
    async def get_character_recipes(self: Self, character_id) -> list[CharacterRecipeReadSchema]:
        async with self.session as s:
            stmt = (
                sa.select(CharacterRecipes)
                .options(joinedload(CharacterRecipes.item))
                .where(CharacterRecipes.character_id == character_id)
                .order_by(CharacterRecipes.created_at.desc())
            )
            
            result = await s.scalars(stmt)
            recipes = result.unique().all()
            
            return [
                CharacterRecipeReadSchema(
                    **{k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')},
                    item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
                )
                for recipe in recipes
            ]
    
    async def get_recipe_price(self: Self, item_slug: str, quantity: int) -> float | None:
        async with self.session as s:
            stmt = (
                sa.select(ItemPrice.price)
                .where(
                    (ItemPrice.item_slug == item_slug) &
                    (ItemPrice.quantity == quantity)
                )
            )
            
            result = await s.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_character_recipe(self: Self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema:
        async with self.session as s:
            # Проверяем существует ли уже такая запись
            stmt_select = (
                sa.select(CharacterRecipes)
                .where(
                    (CharacterRecipes.character_id == character_id) &
                    (CharacterRecipes.item_slug == item_slug)
                )
            )
            result = await s.execute(stmt_select)
            existing_recipe = result.scalar_one_or_none()
            
            if existing_recipe:
                # Обновляем существующую запись, прибавляя quantity
                stmt_update = (
                    sa.update(CharacterRecipes)
                    .where(CharacterRecipes.id == existing_recipe.id)
                    .values(quantity=CharacterRecipes.quantity + quantity)
                    .returning(CharacterRecipes.id)
                )
                await s.execute(stmt_update)
                recipe_id = existing_recipe.id
            else:
                # Создаём новую запись
                stmt_insert = (
                    sa.insert(CharacterRecipes)
                    .values(
                        character_id=character_id,
                        item_slug=item_slug,
                        quantity=quantity
                    )
                    .returning(CharacterRecipes.id)
                )
                result_insert = await s.execute(stmt_insert)
                recipe_id = result_insert.scalar_one()
            
            await s.commit()
            
            # Загружаем полную запись с item для ответа
            stmt_final = (
                sa.select(CharacterRecipes)
                .options(joinedload(CharacterRecipes.item))
                .where(CharacterRecipes.id == recipe_id)
            )
            result_final = await s.execute(stmt_final)
            recipe_with_item = result_final.scalar_one()
            
            # Создаём словарь без поля item из __dict__
            recipe_dict = {k: v for k, v in recipe_with_item.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return CharacterRecipeReadSchema(
                **recipe_dict,
                item=ItemReadSchema.model_validate(recipe_with_item.item, from_attributes=True)
            )
    
    async def get_by_character_item_and_quantity(self: Self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema | None:
        """Получает рецепт персонажа по item_slug и quantity или None если не найден."""
        async with self.session as s:
            stmt = (
                sa.select(CharacterRecipes)
                .options(joinedload(CharacterRecipes.item))
                .where(
                    (CharacterRecipes.character_id == character_id) &
                    (CharacterRecipes.item_slug == item_slug) &
                    (CharacterRecipes.quantity == quantity)
                )
            )
            
            result = await s.execute(stmt)
            recipe = result.scalar_one_or_none()
            
            if recipe is None:
                return None
            
            recipe_dict = {k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return CharacterRecipeReadSchema(
                **recipe_dict,
                item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
            )
    
    async def get_for_character(self: Self, recipe_id, character_id) -> CharacterRecipeReadSchema | None:
        """Получает рецепт персонажа по recipe_id и character_id или None если не найден."""
        async with self.session as s:
            stmt = (
                sa.select(CharacterRecipes)
                .options(joinedload(CharacterRecipes.item))
                .where(
                    (CharacterRecipes.id == recipe_id) &
                    (CharacterRecipes.character_id == character_id)
                )
            )
            
            result = await s.execute(stmt)
            recipe = result.scalar_one_or_none()
            
            if recipe is None:
                return None
            
            recipe_dict = {k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')}
            
            return CharacterRecipeReadSchema(
                **recipe_dict,
                item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
            )

    async def decrement_quantity_for_character(self: Self, recipe_id, character_id) -> bool:
        """Уменьшает quantity рецепта персонажа на 1. Если quantity становится 0, удаляет запись."""
        async with self.session as s:
            stmt_select = (
                sa.select(CharacterRecipes)
                .where(
                    (CharacterRecipes.id == recipe_id) &
                    (CharacterRecipes.character_id == character_id)
                )
            )
            recipe = (await s.execute(stmt_select)).scalar_one_or_none()
            if recipe is None:
                return False

            if recipe.quantity <= 1:
                stmt_delete = sa.delete(CharacterRecipes).where(CharacterRecipes.id == recipe_id)
                result = await s.execute(stmt_delete)
            else:
                stmt_update = (
                    sa.update(CharacterRecipes)
                    .where(CharacterRecipes.id == recipe_id)
                    .values(quantity=CharacterRecipes.quantity - 1)
                )
                result = await s.execute(stmt_update)

            await s.commit()

            return result.rowcount > 0
    
    async def delete_by_character_item_and_quantity(self: Self, character_id, item_slug: str, quantity: int) -> bool:
        """Удаляет рецепт персонажа по item_slug и quantity. Возвращает True если удалено."""
        async with self.session as s:
            stmt = (
                sa.delete(CharacterRecipes)
                .where(
                    (CharacterRecipes.character_id == character_id) &
                    (CharacterRecipes.item_slug == item_slug) &
                    (CharacterRecipes.quantity == quantity)
                )
            )
            
            result = await s.execute(stmt)
            await s.commit()
            
            return result.rowcount > 0

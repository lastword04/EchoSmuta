import asyncio
import uuid
from decimal import Decimal
from typing import Protocol, Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.item_events import ItemMessageEventSchema, ItemMessageScope

from .....core.utils.exceptions import ModelFieldNotFoundException
from ....resources.models import CharacterResource
from ...adapters.characters import CharacterServiceClientProtocol
from ...events.items import ItemEventsProtocol
from ...exceptions import NotEnoughDucatsError
from ...models import Item, ItemPrice
from ...repositories.building.building import BuildingRepositoryProtocol
from ...repositories.items.items import ItemRepositoryProtocol
from ...repositories.items.items_component import ItemComponentRepositoryProtocol
from ...repositories.recipes.character_recipes import CharacterRecipesRepositoryProtocol
from ...schemas import (
    CharacterRecipeReadSchema,
    CharacterRecipeWithDetailsSchema,
    CharacterRecipeWithStockSchema,
    ItemComponentWithResourceAndStockSchema,
    ItemDetailsSchema,
    ItemDetailsWithStockSchema,
    ResourceItemReadSchema,
)
from ...services.adapters.item_templates import ItemTemplateServiceProtocol


class CharacterRecipesServiceProtocol(Protocol):
    async def get_all_recipes(self: Self, location_slug: str, quantity: int) -> list[ResourceItemReadSchema]:
        ...
    
    async def get_character_recipes(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeReadSchema]:
        ...
    
    async def buy_recipe(self: Self, character_id: uuid.UUID, item_slug: str, quantity: int) -> CharacterRecipeReadSchema:
        ...

    async def get_character_recipes_with_details(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeWithDetailsSchema]:
        ...

    async def get_character_recipes_with_stock(self: Self, character_id: uuid.UUID, location_slug: str | None = None) -> list[CharacterRecipeWithStockSchema]:
        ...

    async def get_character_creating_items_with_stock(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeWithStockSchema]:
        ...

class CharacterRecipesService(CharacterRecipesServiceProtocol):
    def __init__(
        self: Self,
        repository: CharacterRecipesRepositoryProtocol,
        character_client: CharacterServiceClientProtocol,
        item_repository: ItemRepositoryProtocol,
        component_repository: ItemComponentRepositoryProtocol,
        session: AsyncSession,
        building_repository: BuildingRepositoryProtocol,
        template_service: ItemTemplateServiceProtocol,
        items_events: ItemEventsProtocol,
    ):
        self.repository = repository
        self.character_client = character_client
        self.item_repository = item_repository
        self.component_repository = component_repository
        self.session = session
        self.building_repository = building_repository
        self.template_service = template_service
        self.items_events = items_events
    
    async def get_all_recipes(self: Self, character_id: uuid.UUID, quantity: int) -> list[ResourceItemReadSchema]:
        location_slug = (await self.character_client.get_simple_character_balance(character_id)).location_slug
        return await self.repository.get_all_recipes(location_slug, quantity)
    
    async def get_character_recipes(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeReadSchema]:
        return await self.repository.get_character_recipes(character_id)
    
    async def buy_recipe(self: Self, character_id: uuid.UUID, item_slug: str, quantity: int) -> CharacterRecipeReadSchema:
        # 1. Получаем цену и баланс параллельно
        price_task = self.repository.get_recipe_price(item_slug, quantity)
        character_task = self.character_client.get_simple_character_balance(character_id)
        
        price, character = await asyncio.gather(price_task, character_task)
        
        if price is None:
            raise ModelFieldNotFoundException(
                model=ItemPrice,
                field="item_slug and quantity",
                value=f"{item_slug} with quantity {quantity}"
            )
        
        if character.ducats < Decimal(str(price)):
            raise NotEnoughDucatsError(
                required_ducats=price,
                current_ducats=character.ducats,
            )
        
        # 2. Проверяем существование рецепта (Item) до списания
        recipe_item = await self.item_repository.get_by_slug(item_slug)
        if recipe_item is None:
            raise ModelFieldNotFoundException(
                model=Item,
                field="item_slug",
                value=item_slug
            )
        
        # 3. Списываем дукаты, теперь recipe_item определена
        await self.character_client.debit_ducats(
            character_id,
            price,
            operation_type="recipe_purchase",
            source=f"mining.{character.location_slug}",
            item_meta={"recipe_slug": recipe_item.slug}  # здесь всё корректно
        )
        
        # 4. Создаём запись о рецепте у персонажа
        recipe = await self.repository.create_character_recipe(character_id, item_slug, quantity)
        
        # 5. Отправляем системное сообщение
        system_message = self.template_service.get_recipe_purchase_message(
            location_slug=recipe.item.location_slug,
            item_name=recipe.item.name,
            quantity=quantity,
            price=f"{price:.2f}",
        )
        await self.items_events.publish_message(
            ItemMessageEventSchema(
                event_type="recipe_purchase",
                character_id=character_id,
                location_slug=recipe.item.location_slug,
                content=system_message,
                scope=ItemMessageScope.PRIVATE,
                target_user_ids=[character_id],
            )
        )

        return recipe

    async def get_character_recipes_with_details(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeWithDetailsSchema]:
        """Получить все рецепты персонажа с детальной информацией об Item и компонентах, отфильтрованные по локации персонажа (последовательные запросы)"""
        character = await self.character_client.get_simple_character_balance(character_id)
        recipes = await self.repository.get_character_recipes(character_id)
        
        result = []
        for recipe in recipes:
            # Последовательно получаем Item и компоненты
            item = await self.item_repository.get_by_slug(recipe.item_slug)
            components = await self.component_repository.get_components_with_resource_names(recipe.item_slug)
            
            if item.location_slug == character.location_slug:
                result.append(
                    CharacterRecipeWithDetailsSchema(
                        recipe_id=recipe.id,
                        quantity=recipe.quantity,
                        item_details=ItemDetailsSchema(
                            item=item,
                            components=components
                        )
                    )
                )
        return result

    async def get_character_recipes_with_stock(self: Self, character_id: uuid.UUID, location_slug: str | None = None) -> list[CharacterRecipeWithStockSchema]:
        """Получить все рецепты персонажа с информацией о наличии ресурсов.

        Фильтр по городской лавке: если передан location_slug — по нему (вкладка
        мастерской может не совпадать с текущей локацией персонажа),
        иначе — по текущей локации персонажа (прежнее поведение).
        """
        character = await self.character_client.get_simple_character_balance(character_id)
        recipes = await self.repository.get_character_recipes(character_id)
        if location_slug:
            building = await self.building_repository.get_by_city_trading_location(location_slug)
        else:
            building = await self.building_repository.get_by_location_slug(character.location_slug)
        
        result = []
        for recipe in recipes:
            # Последовательно получаем Item и компоненты
            item = await self.item_repository.get_by_slug(recipe.item_slug)
            components = await self.component_repository.get_components_with_resource_names(recipe.item_slug)
            
            if building and item.location_slug == building.city_trading_location_slug:
                components_with_stock = []
                for component in components:
                    stmt = select(CharacterResource).where(
                        CharacterResource.character_id == character_id,
                        CharacterResource.resource_slug == component.resource_slug
                    )
                    result_db = await self.session.execute(stmt)
                    char_resource = result_db.scalar_one_or_none()
                    is_in_stock = char_resource is not None and char_resource.amount >= component.quantity
                    
                    components_with_stock.append(
                        ItemComponentWithResourceAndStockSchema(
                            id=component.id,
                            item_slug=component.item_slug,
                            resource_slug=component.resource_slug,
                            quantity=component.quantity,
                            resource_name=component.resource_name,
                            is_in_stock=is_in_stock
                        )
                    )
                
                result.append(
                    CharacterRecipeWithStockSchema(
                        id=recipe.id,
                        recipe_id=recipe.id,
                        quantity=recipe.quantity,
                        item_details=ItemDetailsWithStockSchema(
                            item=item,
                            components=components_with_stock
                        )
                    )
                )
        return result

    async def get_character_creating_items_with_stock(self: Self, character_id: uuid.UUID) -> list[CharacterRecipeWithStockSchema]:
        """Получает список предметов в процессе крафта с информацией о наличии ресурсов (последовательные запросы)"""
        from ...models import CharacterStartCreatingItem
        
        character = await self.character_client.get_simple_character_balance(character_id)
        
        async with self.session as session:
            stmt = select(CharacterStartCreatingItem).where(CharacterStartCreatingItem.character_id == character_id)
            result_db = await session.execute(stmt)
            creating_items = result_db.scalars().all()
        
        if not creating_items:
            return []
        
        result = []
        for creating_item in creating_items:
            # Последовательно получаем информацию
            item = await self.item_repository.get_by_slug(creating_item.item_slug)
            building = await self.building_repository.get_by_city_trading_location(item.location_slug)
            if building.location_slug != character.location_slug:
                continue
            
            components = await self.component_repository.get_components_with_resource_names(creating_item.item_slug)
            if components:
                components_with_stock = []
                for component in components:
                    stmt = select(CharacterResource).where(
                        CharacterResource.character_id == character_id,
                        CharacterResource.resource_slug == component.resource_slug
                    )
                    result_db = await self.session.execute(stmt)
                    char_resource = result_db.scalar_one_or_none()
                    is_in_stock = char_resource is not None and char_resource.amount >= component.quantity
                    
                    components_with_stock.append(
                        ItemComponentWithResourceAndStockSchema(
                            id=component.id,
                            item_slug=component.item_slug,
                            resource_slug=component.resource_slug,
                            quantity=component.quantity,
                            resource_name=component.resource_name,
                            is_in_stock=is_in_stock
                        )
                    )
                
                result.append(
                    CharacterRecipeWithStockSchema(
                        id=creating_item.id,
                        recipe_id=creating_item.id,
                        quantity=None,
                        craft_stage=creating_item.craft_stage,
                        item_details=ItemDetailsWithStockSchema(
                            item=item,
                            components=components_with_stock
                        )
                    )
                )
        return result
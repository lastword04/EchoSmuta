import sqlalchemy as sa
from sqlalchemy.orm import Session, contains_eager, joinedload

from ....resources.models import Resource
from ...models import CharacterRecipes, Item, ItemComponent, ItemPrice
from ...schemas import (
    CharacterRecipeReadSchema,
    ItemComponentWithResourceSchema,
    ItemReadSchema,
    ResourceItemWithComponentsReadSchema,
)


class CharacterRecipesSyncRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_recipes(self, location_slug: str, quantity: int) -> list[ResourceItemWithComponentsReadSchema]:
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
        items = self.session.execute(stmt).scalars().unique().all()
        items = [item for item in items if item.prices]
        if not items:
            return []

        slugs = [item.slug for item in items]
        components_stmt = (
            sa.select(ItemComponent, Resource.name.label("resource_name"))
            .join(Resource, ItemComponent.resource_slug == Resource.slug)
            .where(ItemComponent.item_slug.in_(slugs))
        )
        components_result = self.session.execute(components_stmt).all()

        components_by_slug: dict[str, list[ItemComponentWithResourceSchema]] = {}
        for component, resource_name in components_result:
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

    def get_character_recipes(self, character_id) -> list[CharacterRecipeReadSchema]:
        stmt = (
            sa.select(CharacterRecipes)
            .options(joinedload(CharacterRecipes.item))
            .where(CharacterRecipes.character_id == character_id)
            .order_by(CharacterRecipes.created_at.desc())
        )
        recipes = self.session.execute(stmt).scalars().unique().all()
        return [
            CharacterRecipeReadSchema(
                **{k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')},
                item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
            )
            for recipe in recipes
        ]

    def get_recipe_price(self, item_slug: str, quantity: int) -> float | None:
        stmt = (
            sa.select(ItemPrice.price)
            .where(
                (ItemPrice.item_slug == item_slug) &
                (ItemPrice.quantity == quantity)
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_character_recipe(self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema:
        stmt_select = (
            sa.select(CharacterRecipes)
            .where(
                (CharacterRecipes.character_id == character_id) &
                (CharacterRecipes.item_slug == item_slug)
            )
        )
        existing_recipe = self.session.execute(stmt_select).scalar_one_or_none()
        if existing_recipe:
            stmt_update = (
                sa.update(CharacterRecipes)
                .where(CharacterRecipes.id == existing_recipe.id)
                .values(quantity=CharacterRecipes.quantity + quantity)
                .returning(CharacterRecipes.id)
            )
            recipe_id = self.session.execute(stmt_update).scalar_one()
        else:
            stmt_insert = (
                sa.insert(CharacterRecipes)
                .values(
                    character_id=character_id,
                    item_slug=item_slug,
                    quantity=quantity
                )
                .returning(CharacterRecipes.id)
            )
            recipe_id = self.session.execute(stmt_insert).scalar_one()

        self.session.flush()

        stmt_final = (
            sa.select(CharacterRecipes)
            .options(joinedload(CharacterRecipes.item))
            .where(CharacterRecipes.id == recipe_id)
        )
        recipe_with_item = self.session.execute(stmt_final).scalar_one()
        recipe_dict = {k: v for k, v in recipe_with_item.__dict__.items() if k != 'item' and not k.startswith('_')}
        return CharacterRecipeReadSchema(
            **recipe_dict,
            item=ItemReadSchema.model_validate(recipe_with_item.item, from_attributes=True)
        )

    def get_by_character_item_and_quantity(self, character_id, item_slug: str, quantity: int) -> CharacterRecipeReadSchema | None:
        stmt = (
            sa.select(CharacterRecipes)
            .options(joinedload(CharacterRecipes.item))
            .where(
                (CharacterRecipes.character_id == character_id) &
                (CharacterRecipes.item_slug == item_slug) &
                (CharacterRecipes.quantity == quantity)
            )
        )
        recipe = self.session.execute(stmt).scalar_one_or_none()
        if recipe is None:
            return None
        recipe_dict = {k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')}
        return CharacterRecipeReadSchema(
            **recipe_dict,
            item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
        )

    def get_for_character(self, recipe_id, character_id) -> CharacterRecipeReadSchema | None:
        stmt = (
            sa.select(CharacterRecipes)
            .options(joinedload(CharacterRecipes.item))
            .where(
                (CharacterRecipes.id == recipe_id) &
                (CharacterRecipes.character_id == character_id)
            )
        )
        recipe = self.session.execute(stmt).scalar_one_or_none()
        if recipe is None:
            return None
        recipe_dict = {k: v for k, v in recipe.__dict__.items() if k != 'item' and not k.startswith('_')}
        return CharacterRecipeReadSchema(
            **recipe_dict,
            item=ItemReadSchema.model_validate(recipe.item, from_attributes=True)
        )

    def decrement_quantity_for_character(self, recipe_id, character_id) -> bool:
        stmt_select = (
            sa.select(CharacterRecipes)
            .where(
                (CharacterRecipes.id == recipe_id) &
                (CharacterRecipes.character_id == character_id)
            )
        )
        recipe = self.session.execute(stmt_select).scalar_one_or_none()
        if recipe is None:
            return False

        if recipe.quantity <= 1:
            stmt_delete = sa.delete(CharacterRecipes).where(CharacterRecipes.id == recipe_id)
            result = self.session.execute(stmt_delete)
        else:
            stmt_update = (
                sa.update(CharacterRecipes)
                .where(CharacterRecipes.id == recipe_id)
                .values(quantity=CharacterRecipes.quantity - 1)
            )
            result = self.session.execute(stmt_update)

        self.session.flush()
        return result.rowcount > 0

    def delete_by_character_item_and_quantity(self, character_id, item_slug: str, quantity: int) -> bool:
        stmt = (
            sa.delete(CharacterRecipes)
            .where(
                (CharacterRecipes.character_id == character_id) &
                (CharacterRecipes.item_slug == item_slug) &
                (CharacterRecipes.quantity == quantity)
            )
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount > 0

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def close(self):
        self.session.close()
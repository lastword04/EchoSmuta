from typing import ClassVar, Protocol

from shared.services.templates import TextTemplateServiceProtocol


class ItemTemplateServiceProtocol(Protocol):
    def get_city_name(self, location_slug: str) -> str:
        ...

    def get_shop_purchase_message(self, location_slug: str, number: int, city_name: str) -> str:
        ...

    def get_shop_purchase_public_message(
        self, location_slug: str, character_name: str, number: int, city_name: str
    ) -> str:
        ...

    def get_item_purchase_buyer_message(self, location_slug: str, item_name: str, price: str) -> str:
        ...

    def get_item_purchase_seller_message(
        self, location_slug: str, item_name: str, price: str, buyer_name: str, tax: str
    ) -> str:
        ...

    def get_license_renewal_message(self, location_slug: str, end_license: str) -> str:
        ...

    def get_level_up_message(self, location_slug: str, level: int) -> str:
        ...

    def get_recipe_purchase_message(
        self, location_slug: str, item_name: str, quantity: int, price: str
    ) -> str:
        ...

    def get_crafting_progress_message(
        self,
        location_slug: str,
        item_name: str,
        stage: int,
        total_stages: int,
        time: int,
    ) -> str:
        ...

    def get_crafting_stage_success_message(
        self, location_slug: str, item_name: str, stage: int
    ) -> str:
        ...

    def get_crafting_stage_failure_message(self, location_slug: str, item_name: str) -> str:
        ...

    def get_crafting_stage_failure_with_loss_message(
        self, location_slug: str, item_name: str, resource_name: str
    ) -> str:
        ...

    def get_crafting_success_message(self, location_slug: str, item_name: str, amount: int) -> str:
        ...

    def get_item_expired_message(self, item_name: str, amount: int = 1) -> str:
        ...

    def get_animal_died_message(self, item_name: str) -> str:
        ...

    def get_trade_license_purchase_message(self) -> str: 
        ...
    def get_trade_license_renewal_message(self, end_license: str) -> str: 
        ...


class ItemTemplateService(ItemTemplateServiceProtocol):
    CITY_KEYS: ClassVar[dict[str, str]] = {
        "1": "Авалон",
    }

    LOCATION_KEYS: ClassVar[dict[str, str]] = {
        "1.9.pharmacy": "pharmacy",
        "1.21.furniture-shop": "furniture_shop",
        "1.22.hunting-shop": "hunting_shop",
        "1.24.bird-market": "bird_market",
        "1.25.fish-shop": "fish_shop",
        "1.13.forge": "forge",
        "1.16.jewelers": "jewelers",
        "1.27.trade-hall": "trade_hall",
    }

    def __init__(self, template_service: TextTemplateServiceProtocol):
        self.template_service = template_service

    def get_city_name(self, location_slug: str) -> str:
        city_key = location_slug.split(".", 1)[0]
        city_name = self.CITY_KEYS.get(city_key)
        if city_name is None:
            raise ValueError(f"Unknown item template city key: {city_key}")

        return city_name

    def get_shop_purchase_message(self, location_slug: str, number: int, city_name: str) -> str:
        return self._get_template(
            location_slug,
            "shop",
            "purchase_self",
            number=number,
            city_name=city_name,
        )

    def get_shop_purchase_public_message(
        self, location_slug: str, character_name: str, number: int, city_name: str
    ) -> str:
        return self._get_template(
            location_slug,
            "shop",
            "purchase_public",
            character_name=character_name,
            number=number,
            city_name=city_name,
        )

    def get_item_purchase_buyer_message(self, location_slug: str, item_name: str, price: str) -> str:
        return self._get_template(
            location_slug,
            "trade",
            "purchase_buyer",
            item_name=item_name,
            price=price,
        )

    def get_item_purchase_seller_message(
        self, location_slug: str, item_name: str, price: str, buyer_name: str, tax: str
    ) -> str:
        return self._get_template(
            location_slug,
            "trade",
            "purchase_seller",
            item_name=item_name,
            price=price,
            buyer_name=buyer_name,
            tax=tax,
        )

    def get_license_renewal_message(self, location_slug: str, end_license: str) -> str:
        return self._get_template(
            location_slug,
            "shop",
            "license_renewal",
            end_license=end_license,
        )

    def get_level_up_message(self, location_slug: str, level: int) -> str:
        return self._get_template(
            location_slug,
            "shop",
            "level_up",
            level=level,
        )

    def get_recipe_purchase_message(
        self, location_slug: str, item_name: str, quantity: int, price: str
    ) -> str:
        return self._get_template(
            location_slug,
            "recipes",
            "purchase",
            item_name=item_name,
            quantity=quantity,
            price=price,
        )

    def get_crafting_progress_message(
        self,
        location_slug: str,
        item_name: str,
        stage: int,
        total_stages: int,
        time: int,
    ) -> str:
        return self._get_template(
            location_slug,
            "crafting",
            "progress",
            item_name=item_name,
            stage=stage,
            total_stages=total_stages,
            time=time,
        )

    def get_crafting_stage_success_message(
        self, location_slug: str, item_name: str, stage: int
    ) -> str:
        return self._get_template(
            location_slug,
            "crafting",
            "stage_success",
            item_name=item_name,
            stage=stage,
        )

    def get_crafting_stage_failure_message(self, location_slug: str, item_name: str) -> str:
        return self._get_template(
            location_slug,
            "crafting",
            "stage_failure",
            item_name=item_name,
        )

    def get_crafting_stage_failure_with_loss_message(
        self, location_slug: str, item_name: str, resource_name: str
    ) -> str:
        return self._get_template(
            location_slug,
            "crafting",
            "stage_failure_with_loss",
            item_name=item_name,
            resource_name=resource_name,
        )

    def get_crafting_success_message(self, location_slug: str, item_name: str, amount: int) -> str:
        return self._get_template(
            location_slug,
            "crafting",
            "success",
            item_name=item_name,
            amount=amount,
        )

    def _get_template(
        self,
        location_slug: str,
        section: str,
        template_name: str,
        **kwargs,
    ) -> str:
        location_key = self.LOCATION_KEYS.get(location_slug)
        if location_key is None:
            raise ValueError(f"Unknown item template location slug: {location_slug}")

        return self.template_service.get_template_by_path(
            ["items", "locations", location_key, section, template_name],
            **kwargs,
        )

    def get_license_purchase_message(self, location_slug: str, end_license: str) -> str:
        return self._get_template(
            location_slug,
            "shop",
            "purchase_self",
            end_license=end_license,
        )

    def get_item_expired_message(self, item_name: str, amount: int = 1) -> str:
        template_key = "item_expired_stack" if amount > 1 else "item_expired"
        return self.template_service.get_template_by_path(
            ["items", "expiry", template_key],
            item_name=item_name,
            amount=amount,
        )

    def get_animal_died_message(self, item_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["items", "expiry", "animal_died"],
            item_name=item_name,
        )

    def get_trade_license_purchase_message(self) -> str:
        return self.template_service.get_template_by_path(
            ["items", "trade_license", "purchase"],
        )

    def get_trade_license_renewal_message(self, end_license: str) -> str:
        return self.template_service.get_template_by_path(
            ["items", "trade_license", "renewal"],
            end_license=end_license,
        )

    def get_consumable_use_message(self, item_name: str) -> str:
        """Сообщение об употреблении рыбы/эликсира"""
        return self.template_service.get_template_by_path(
            ["items", "consumable", "use"],
            item_name=item_name,
        )

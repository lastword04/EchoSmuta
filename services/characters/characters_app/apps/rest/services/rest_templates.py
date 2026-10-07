from typing import ClassVar, Protocol

from shared.services.templates import TextTemplateServiceProtocol


class RestTemplateServiceProtocol(Protocol):
    def get_rent_message(self, inn_name: str, days_text: str) -> str: ...
    def get_expired_message(self, inn_name: str) -> str: ...
    def get_city_name(self, location_slug: str) -> str: ...
    def get_house_purchase_self_message(self, number: int, city_name: str) -> str: ...
    def get_house_purchase_public_message(self, character_name: str, number: int, city_name: str) -> str: ...
    def get_house_knock_message(self, number: int) -> str: ...
    def get_house_accepted_guest_message(self, number: int) -> str: ...
    def get_house_accepted_owner_message(self, character_name: str) -> str: ...
    def get_house_kicked_owner_message(self, character_name: str) -> str: ...


class RestTemplateService(RestTemplateServiceProtocol):
    CITY_KEYS: ClassVar[dict[str, str]] = {
        "1": "Авалон",
    }

    def __init__(self, template_service: TextTemplateServiceProtocol):
        self.template_service = template_service

    def get_rent_message(self, inn_name: str, days_text: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "rent"],
            inn_name=inn_name,
            days_text=days_text,
        )

    def get_expired_message(self, inn_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "expired"],
            inn_name=inn_name,
        )

    def get_city_name(self, location_slug: str) -> str:
        city_key = location_slug.split(".", 1)[0]
        city_name = self.CITY_KEYS.get(city_key)
        if city_name is None:
            raise ValueError(f"Unknown city key: {city_key}")
        return city_name

    def get_house_purchase_self_message(self, number: int, city_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "purchase_self"],
            number=number,
            city_name=city_name,
        )

    def get_house_purchase_public_message(self, character_name: str, number: int, city_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "purchase_public"],
            character_name=character_name,
            number=number,
            city_name=city_name,
        )

    def get_house_knock_message(self, number: int) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "knock_self"],
            number=number,
        )

    def get_house_accepted_guest_message(self, number: int) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "accepted_guest"],
            number=number,
        )

    def get_house_accepted_owner_message(self, character_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "accepted_owner"],
            character_name=character_name,
        )

    def get_house_kicked_owner_message(self, character_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["rest", "house", "kicked_owner"],
            character_name=character_name,
        )
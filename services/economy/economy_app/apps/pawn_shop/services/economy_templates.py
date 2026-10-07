from typing import Protocol

from shared.services.templates import TextTemplateServiceProtocol
from shared.utils.plural import plural


class EconomyTemplateServiceProtocol(Protocol):
    def get_buyout_buy_message(self, items_list: str, price: str) -> str:
        ...

    def get_buyout_sell_message(self, items_list: str, price: str) -> str:
        ...

    def get_exchange_deal_buy_executor_message(self, items: str, price: str) -> str:
        ...

    def get_exchange_deal_sell_executor_message(self, items: str, price: str, tax: str) -> str:
        ...

    def get_exchange_deal_sell_owner_message(self, items: str, price: str, executor_name: str, tax: str) -> str:
        ...

    def get_exchange_deal_buy_owner_message(self, items: str, price: str, executor_name: str) -> str:
        ...


class EconomyTemplateService(EconomyTemplateServiceProtocol):
    def __init__(self, template_service: TextTemplateServiceProtocol):
        self.template_service = template_service

    def _plural_briquet(self, n: int) -> str:
        return plural(n, "брикет", "брикета", "брикетов")

    def get_buyout_buy_message(self, items_list: str, price: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "buyout", "buy"],
            items_list=items_list,
            price=price,
        )

    def get_buyout_sell_message(self, items_list: str, price: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "buyout", "sell"],
            items_list=items_list,
            price=price,
        )

    def get_exchange_deal_buy_executor_message(self, items: str, price: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "exchange", "deal_buy_executor"],
            items=items,
            price=price,
        )

    def get_exchange_deal_sell_executor_message(self, items: str, price: str, tax: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "exchange", "deal_sell_executor"],
            items=items,
            price=price,
            tax=tax,
        )

    def get_exchange_deal_sell_owner_message(self, items: str, price: str, executor_name: str, tax: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "exchange", "deal_sell_owner"],
            items=items,
            price=price,
            executor_name=executor_name,
            tax=tax,
        )

    def get_exchange_deal_buy_owner_message(self, items: str, price: str, executor_name: str) -> str:
        return self.template_service.get_template_by_path(
            ["economy", "pawnshop", "exchange", "deal_buy_owner"],
            items=items,
            price=price,
            executor_name=executor_name,
        )

    def get_tavern_buy_message(self, meal_name: str, price: str) -> str:
        """Сообщение о покупке блюда в харчевне"""
        return self.template_service.get_template_by_path(
            ["economy", "tavern", "buy"],
            meal_name=meal_name,
            price=price,
        )

    
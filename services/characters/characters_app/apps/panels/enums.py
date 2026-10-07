from enum import Enum


class MenuItem(str, Enum):
    """
    Перечисление всех возможных Item, которые можно закрепить в быстром доступе сверху на заборе.
    Enum используется в БД, если обновлять его здесь, то надо вручную исправлять миграции, т.к. alembic
    не регистрирует изменения в enum`ах
    """
    MAP = "map"
    INVENTORY = "inventory"
    PARAMETERS = "parameters"
    MAGIC = "magic"
    FRIENDS = "friends"
    SETTINGS = "settings"
    CAMPAIGN = "campaign"
    EARN = "earn"
    NOTEBOOK = "notebook"
    CABINET = "cabinet"
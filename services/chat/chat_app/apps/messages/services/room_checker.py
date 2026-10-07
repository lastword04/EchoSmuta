from typing import Protocol
from shared.enums import UserRole 
from ..adapter.locations import LocationsServiceClientProtocol
from ....core.utils.exceptions import PermissionDeniedError
class RoomCheckerProtocol(Protocol):
    async def is_room_valid(self, room: str, user_role: UserRole) -> bool:
        ...

class RoomChecker(RoomCheckerProtocol):
    def __init__(self, locations_client: LocationsServiceClientProtocol, valid_rooms: list[str]):
        self.locations_client = locations_client
        self.valid_rooms = valid_rooms

    async def is_room_valid(self, room: str, user_role: UserRole) -> bool:
        if room == "system" and (user_role not in [UserRole.ADMIN, UserRole.MODERATOR]):
            raise PermissionDeniedError()

        # Виртуальные комнаты: дом ('house:<uuid>') и номер гостиницы ('inn:inside').
        # Это не локации из таблицы locations, но и не «мусорные» комнаты —
        # их создаёт бэкенд characters при входе в дом/номер. Считаем валидными.
        # Позже, если понадобится access control (например, «в чужом доме
        # историю не видно»), можно добавить проверку через characters API.
        if room.startswith("house:") or room == "inn:inside":
            return True

        if room in self.valid_rooms:
            return True
        location = await self.locations_client.get_by_slug(room)
        return bool(location)
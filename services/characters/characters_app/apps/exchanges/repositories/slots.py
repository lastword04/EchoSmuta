from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import Slot
from ..schemas import (
    SlotCreateDBSchema,
    SlotReadDBSchema,
    SlotUpdateDBSchema,
)

class SlotRepositoryProtocol(
    BaseRepositoryImpl[
        Slot,
        SlotReadDBSchema,
        SlotCreateDBSchema,
        SlotUpdateDBSchema
    ]
):
    pass

class SlotRepository(SlotRepositoryProtocol):
    pass
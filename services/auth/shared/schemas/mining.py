import uuid
from pydantic import BaseModel
from ..enums import ResultStatus

class MonsterAttackEventSchema(BaseModel):
    monster_name: str
    is_standart_monster: bool
    is_win: bool

class MiningActionEventSchema(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    location_slug: str
    result_status: ResultStatus | None = None
    recived_resourse_slug: str | None = None
    recived_resourse_name: str | None = None
    count_recived_resource: int | None = None
    monster_attack: MonsterAttackEventSchema | None = None
from pydantic import BaseModel

class BaseCategoryStatsSchema(BaseModel):
    friends_count: int
    enemies_count: int
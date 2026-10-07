from .apps.forum.depends import (
    get_initialize_forum_use_case,
)
from .core.db import AsyncSession

async def initialize_forums(session: AsyncSession) -> None:
    use_case = get_initialize_forum_use_case(session=session)
    await use_case()


async def initialize_app(session: AsyncSession) -> None:
    """
    Инициализация приложения, включая создание форумов, которые уже есть.
    """
    await initialize_forums(session=session)

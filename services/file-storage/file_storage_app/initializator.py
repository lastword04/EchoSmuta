from .apps.files.depends import (
    get_file_create_if_not_exist_use_case,
)
from .core.db import AsyncSession

async def initialize_files(session: AsyncSession) -> None:
    use_case = get_file_create_if_not_exist_use_case(session=session)
    await use_case()


async def initialize_app(session: AsyncSession) -> None:
    """
    Инициализация приложения, включая создание файлов, которые уже есть.
    """
    await initialize_files(session=session)

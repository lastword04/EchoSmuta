from .apps.characters.deps import (
    get_initialize_race_settings_use_case,
    get_initialize_global_character_settings_use_case,
    get_initialize_global_character_experience_settings_use_case,
    get_initialize_character_attachment_settings_use_case_dep,
    get_initialize_transfer_value_settings_use_case_dep,
    get_initialize_cities_use_case,
    get_initialize_locations_use_case,
)
from .apps.exchanges.depends import get_initialize_exchange_settings_use_case
from .core.db import AsyncSession

async def initialize_race_settings(session: AsyncSession) -> None:
    use_case = get_initialize_race_settings_use_case(session=session)
    await use_case()

async def initialize_global_character_settings(session: AsyncSession) -> None:
    use_case = get_initialize_global_character_settings_use_case(session=session)
    await use_case()

async def initialize_global_character_experience_settings(session: AsyncSession) -> None:
    use_case = get_initialize_global_character_experience_settings_use_case(session=session)
    await use_case()

async def initialize_character_attachment_settings(session: AsyncSession) -> None:
    use_case = get_initialize_character_attachment_settings_use_case_dep(session=session)
    await use_case()

async def initialize_transfer_value_settings(session: AsyncSession) -> None:
    use_case = get_initialize_transfer_value_settings_use_case_dep(session=session)
    await use_case()

async def initialize_exchange_settings(session: AsyncSession) -> None:
    use_case = get_initialize_exchange_settings_use_case(session=session)
    await use_case()

async def initialize_cities(session: AsyncSession) -> None:
    use_case = get_initialize_cities_use_case(session=session)
    await use_case()

async def initialize_locations(session: AsyncSession) -> None:
    use_case = get_initialize_locations_use_case(session=session)
    await use_case()

async def initialize_app(session: AsyncSession) -> None:
    """
    Инициализация приложения, включая инициализацию настроек рас.
    """
    await initialize_race_settings(session=session)

    await initialize_global_character_settings(session=session)

    await initialize_global_character_experience_settings(session=session)

    await initialize_character_attachment_settings(session=session)

    await initialize_transfer_value_settings(session=session)

    await initialize_exchange_settings(session=session)

    await initialize_cities(session=session)

    await initialize_locations(session=session)
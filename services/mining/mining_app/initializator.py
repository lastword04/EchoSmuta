from .apps.items.deps.initializators import (
    get_init_buildings_use_case,
    get_init_city_trading_shop_buy_settings_use_case,
    get_init_city_trading_shop_settings_use_case,
    get_init_item_components_use_case,
    get_init_item_experience_for_level_use_case,
    get_init_items_price_use_case,
    get_init_items_use_case,
)
from .apps.resources.depends import (
    get_initialize_experience_for_level_use_case,
    get_initialize_location_resources_use_case,
    get_initialize_location_settings_use_case,
    get_initialize_monsters_use_case,
    get_initialize_resources,
)
from .core.db import AsyncSession


async def initialize_resources(session: AsyncSession) -> None:
    use_case = get_initialize_resources(session)
    await use_case()

async def initialize_items(session: AsyncSession) -> None:
    use_case = get_init_items_use_case(session)
    await use_case()

async def initialize_items_price(session: AsyncSession) -> None:
    use_case = get_init_items_price_use_case(session=session)
    await use_case()

async def initialize_items_component(session: AsyncSession) -> None:
    use_case = get_init_item_components_use_case(session=session)
    await use_case()

async def initialize_city_trading_settings(session: AsyncSession) -> None:
    use_case = get_init_city_trading_shop_settings_use_case(session=session)
    await use_case()

async def initialize_city_trading_buy_settings(session: AsyncSession) -> None:
    use_case = get_init_city_trading_shop_buy_settings_use_case(session=session)
    await use_case()

async def initialize_location_resources(session: AsyncSession) -> None:
    use_case = get_initialize_location_resources_use_case(session=session)
    await use_case()

async def initialize_experience_for_level(session: AsyncSession) -> None:
    use_case = get_initialize_experience_for_level_use_case(session=session)
    await use_case()

async def initialize_location_settings(session: AsyncSession) -> None:
    use_case = get_initialize_location_settings_use_case(session)
    await use_case()

async def initialize_monsters(session: AsyncSession) -> None:
    use_case = get_initialize_monsters_use_case(session)
    await use_case()

async def initialize_items_experience_for_level(session: AsyncSession) -> None:
    use_case = get_init_item_experience_for_level_use_case(session=session)
    await use_case()

async def initialize_buildings(session: AsyncSession) -> None:
    use_case = get_init_buildings_use_case(session=session)
    await use_case()

async def initialize_app(session: AsyncSession) -> None:
    """
    Инициализация приложения, включая инициализацию настроек ресурсов.
    """

    await initialize_resources(session=session)

    await initialize_items(session=session)

    await initialize_items_price(session=session)

    await initialize_items_component(session=session)

    await initialize_city_trading_settings(session=session)

    await initialize_city_trading_buy_settings(session=session)

    await initialize_location_resources(session=session)

    await initialize_experience_for_level(session=session)

    await initialize_location_settings(session=session)

    await initialize_monsters(session=session)

    await initialize_items_experience_for_level(session=session)

    await initialize_buildings(session=session)
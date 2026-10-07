from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import ResourceCreateSchema, ResourceReadSchema
from ...services.resources import ResourceServiceProtocol


class InitializeResourcesUseCaseProtocol(UseCaseProtocol[list[ResourceReadSchema]]):
    async def __call__(self: Self) -> list[ResourceReadSchema]:
        ...


class InitializeResourcesUseCase(InitializeResourcesUseCaseProtocol):
    def __init__(self: Self, service: ResourceServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[ResourceReadSchema]:

        used_resources = await self.service.get_all()
        default_resources = self._get_default_resources()
        if len(used_resources) == len(default_resources):
            return used_resources
        if len(used_resources) != 0:
            raise ValueError("Resources not corrected count.")

        return await self.service.bulk_create(default_resources)

    def _get_default_resources(self: Self) -> list[ResourceCreateSchema]:

        # Номера локаций - последний столбец и выглядит так:
        # Болото 1
        # Шахта 2
        # Прииск 3
        # Озеро 4
        # Лес 5
        # Пески 6

        resource_data = [
            # БОЛОТО (Собирать) 1
            ("Подорожник", "plantain", 0, 1, 1),
            ("Пустырник", "motherwort", 0, 1, 1),
            ("Зверобой", "hypericum", 0, 1, 1),
            ("Мать-и-мачеха", "coltsfoot", 0, 1, 1),
            ("Чистотел", "celandine", 0, 1, 1),
            ("Мята", "mint", 0, 1, 1),
            ("Чертополох", "thistle", 0, 1, 1),
            ("Тысячелистник", "yarrow", 0, 1, 1),
            ("Женьшень", "ginseng", 0, 1, 1),
            ("Трын-трава", "tryn-trava", 0, 1, 1),

            # ШАХТА (Копать - Руда) 2
            ("Железо", "iron", 0, 1, 2),
            ("Сера", "sulfur", 0, 1, 2),
            ("Медь", "copper", 0, 1, 2),
            ("Кремний", "silicon", 0, 1, 2),
            ("Слюда", "mica", 0, 1, 2),
            ("Цинк", "zinc", 0, 1, 2),
            ("Свинец", "lead", 0, 1, 2),
            ("Олово", "tin", 0, 1, 2),

            # ПРИИСК (Добывать - Самоцветы) 3
            ("Топаз", "topaz", 0, 1, 3),
            ("Аметист", "amethyst", 0, 1, 3),
            ("Опал", "opal", 0, 1, 3),
            ("Сапфир", "sapphire", 0, 1, 3),
            ("Изумруд", "emerald", 0, 1, 3),
            ("Рубин", "ruby", 0, 1, 3),
            ("Алмаз", "diamond", 0, 1, 3),

            # ОЗЕРО (Забросить - Рыба) 4
            ("Ёрш", "goby", 0, 1, 4),
            ("Плотва", "roach", 0, 1, 4),
            ("Карась", "crucian", 0, 1, 4),
            ("Карп", "carp", 0, 1, 4),
            ("Щука", "pike", 0, 1, 4),
            ("Сом", "catfish", 0, 1, 4),
            ("Осётр", "sturgeon", 0, 1, 4),

            # ЛЕС (Рубить - Деревья) 5
            ("Бук", "beech", 0, 1, 5),
            ("Дуб", "oak", 0, 1, 5),
            ("Берёза", "birch", 0, 1, 5),
            ("Ель", "spruce", 0, 1, 5),
            ("Красное дерево", "mahogany", 0, 1, 5),
            
            # ПЕСКИ (Исследовать - Находки) 6
            ("Метеоритная пыль", "meteor-dust", 0, 1, 6),
            ("Пустынный нектар", "desert-nectar", 0, 1, 6),
            ("Перо дракона", "dragon-feather", 0, 1, 6),
            ("Яйцо дракона", "dragon-egg", 0, 1, 6),
            ("Зачарованная вода", "enchanted-water", 0, 1, 6),
            ("Чешуя дракона", "dragon-scale", 0, 1, 6),
            ("Солнечный кристалл", "sun-crystal", 0, 1, 6),

            # Шкуры монстров
            # Тут тоже последний стобец - лока, где он выпадает
            ("Шкура Зверожаба", "skin-zverozhab", 0, 1, 1),
            ("Шкура Лорда Зверожаба", "skin-lord-zverozhab", 0, 1, 1),
            ("Шкура Гро", "skin-gro", 0, 1, 2),
            ("Шкура Большого Гро", "skin-big-gro", 0, 1, 2),
            ("Шкура Златоглава", "skin-zlatoglav", 0, 1, 3),
            ("Шкура Златогрыза", "skin-zlatogriz", 0, 1, 3),
            ("Шкура Шишиги", "skin-shishiga", 0, 1, 4),
            ("Шкура Морены", "skin-morena", 0, 1, 4),
            ("Шкура Клювозуба", "skin-kluvozyb", 0, 1, 5),
            ("Шкура Клювоклыка", "skin-kluvoklik", 0, 1, 5),
            ("Шкура Скорпиона", "skin-skorpion", 0, 1, 6),
            ("Шкура Красного Скорпиона", "skin-red-skorpion", 0, 1, 6),
        ]

        all_resources = []
        for number, resource in enumerate(resource_data):
            r_name, r_slug, r_weight, r_price, r_location_number = resource
            all_resources.append(
                ResourceCreateSchema(
                    name=r_name,
                    slug=f"i.r.{r_location_number}.3.{r_slug}",
                    weight=r_weight,
                    price=r_price,
                    serial_number=number+1
                )
            )

        return all_resources
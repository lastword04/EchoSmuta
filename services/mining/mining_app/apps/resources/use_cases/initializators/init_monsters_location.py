from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import MonsterLocationCreateSchema, MonsterLocationReadSchema
from ...services.monster_location import MonsterLocationServiceProtocol


class InitializeMonsterLocationUseCaseProtocol(UseCaseProtocol[list[MonsterLocationReadSchema]]):
    async def __call__(self: Self) -> list[MonsterLocationReadSchema]:
        ...


class InitializeMonsterLocationUseCase(InitializeMonsterLocationUseCaseProtocol):
    def __init__(self: Self, service: MonsterLocationServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> list[MonsterLocationReadSchema]:
        used_monsters = await self.service.get_all()
        default_monsters = self._get_default_monsters(2)
        if len(used_monsters) == len(default_monsters):
            return used_monsters
        if len(used_monsters) != 0:
            raise ValueError("Resources not corrected count.")

        return await self.service.bulk_create(default_monsters)

    def _get_default_monsters(self: Self, city_number: int) -> list[MonsterLocationCreateSchema]:
        # Номера локаций по умолчанию:
        # Болото 1
        # Шахта 2
        # Прииск 3
        # Озеро 4
        # Лес 5
        # Пески 6
        resource_data = [
            (1, "swamp", "Зверожаб", "skin-zverozhab", "Лорд Зверожаб", "skin-lord-zverozhab"),
            (2, "shaft", "Гро", "skin-gro", "Большой Гро", "skin-big-gro"),
            (3, "mine", "Златоглав", "skin-zlatoglav", "Златогрыз", "skin-zlatogriz"),
            (4, "lake", "Шишига", "skin-shishiga", "Морена", "skin-morena"),
            (5, "forest", "Клювозуб", "skin-kluvozyb", "Клювоклык", "skin-kluvoklik"),
            (6, "sands", "Скорпион", "skin-skorpion", "Красный Скорпион", "skin-red-skorpion"),
        ]

        return [
            MonsterLocationCreateSchema(
                location_slug=f"{city_number}.{r_number_loc}.{r_slug}",
                standart_monster_name=r_standart_name,
                standart_monster_skin_slug=f"i.r.{r_number_loc}.3.{r_standart_skin}",
                improved_monster_name=r_improved_name,
                improved_monster_skin_slug=f"i.r.{r_number_loc}.3.{r_improved_skin}"
            )
            for r_number_loc, r_slug, r_standart_name, r_standart_skin, r_improved_name, r_improved_skin in resource_data
        ]
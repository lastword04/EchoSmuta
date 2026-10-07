from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol 
from ..enums import ForumSection
from ..schemas import ForumCreateDBSchema, ForumReadSchema
from ..services.forum import ForumServiceProtocol 


class InitializeForumUseCaseProtocol(UseCaseProtocol[ForumReadSchema]):
    async def __call__(self: Self) -> ForumReadSchema:
        ...


class InitializeForumUseCase(InitializeForumUseCaseProtocol):
    def __init__(self: Self, service: ForumServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> ForumReadSchema:

        forums = await self.service.get_all()
        default_forums = self._get_default_forums()
        if len(forums) == len(default_forums):
            return forums

        return await self.service.bulk_create(default_forums)

    def _get_default_forums(self: Self) -> list[ForumCreateDBSchema]:
        return [
            ForumCreateDBSchema(
                name="Ложа Серебряной пули",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Ложа Изгнания",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Ложа Хранителей Мудрости",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Ложа Дозора",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Ложа Вестителей",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Ложа Модерации",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Приемная ОСИ",
                section=ForumSection.MODERATION,
            ),
            ForumCreateDBSchema(
                name="Графика и дизайн",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Политика - Официальные заявления",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Политика - Переговоры",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Финансовое развитие проекта",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Форум - идеи и предложения",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Игра - идеи и предложения",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Игра - глюки и баги",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Турниры и конкурсы",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Торговля",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Доска объявлений",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Общий форум по игре",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Игра - правила",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Новости",
                section=ForumSection.GAME,
            ),
            ForumCreateDBSchema(
                name="Дневники...",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Пряздрявляю...",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Спортклуб",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Депресс-клуб",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Игры, задачи и головоломки",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Флуд",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Литература и критика",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Клуб знакомств Эхо Смуты",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Форум по неигровым вопросам",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Встречи в реале",
                section=ForumSection.OFF_TOPIC,
            ),
            ForumCreateDBSchema(
                name="Старые друзья",
                section=ForumSection.OFF_TOPIC,
            ),
        ]
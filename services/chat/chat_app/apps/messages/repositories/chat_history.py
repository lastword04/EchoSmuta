import uuid
import sqlalchemy as sa
from datetime import datetime, timedelta, timezone
from typing import Optional
from typing_extensions import Self
from sqlalchemy import and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.schemas.base import PaginationSchema
from ...categories.models import Category, CategoryCharacter
from ..models import Message, ChatSettings, Ignore
from ..schemas import MessagePaginationReadSchema, MessageReadSchema


CHAT_HISTORY_RETENTION_DAYS = 1

class ChatHistoryRepositoryProtocol:
    async def get_chat_history(
        self: Self, 
        character_id: uuid.UUID, 
        room: str,
        location_slug: Optional[str],
        pagination: PaginationSchema
    ) -> MessagePaginationReadSchema:
        ...

class ChatHistoryRepository(ChatHistoryRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def get_chat_history(
        self: Self, 
        character_id: uuid.UUID, 
        room: str,
        location_slug: Optional[str],
        pagination: PaginationSchema
    ) -> MessagePaginationReadSchema:
        async with self.session as session:
            # Получаем настройки чата
            settings_stmt = sa.select(
                ChatSettings.filter_trade_messages,
                ChatSettings.filter_system_messages,
                ChatSettings.filter_only_me_and_my,
                ChatSettings.filter_location_messages
            ).where(
                ChatSettings.character_id == character_id
            )
            settings_result = await session.execute(settings_stmt)
            settings_row = settings_result.fetchone()
            
            if settings_row:
                show_trade_messages = settings_row[0]
                show_system_messages = settings_row[1]
                filter_only_me_and_my = settings_row[2]
                show_location_messages = settings_row[3]
            else:
                show_trade_messages = True
                show_system_messages = True
                filter_only_me_and_my = False
                show_location_messages = False

            # Получаем список игнорируемых персонажей
            ignored_query = sa.select(Ignore.ignored_character_id).where(
                Ignore.character_id == character_id
            )
            ignored_result = await session.execute(ignored_query)
            ignored_ids = [row[0] for row in ignored_result.fetchall()]
            ignored_set = set(ignored_ids) if ignored_ids else set()

            # Основные условия фильтрации для НЕ системных сообщений
            base_conditions = []

            # Единый фильтр по времени для всех сообщений
            cutoff = datetime.now(timezone.utc) - timedelta(days=CHAT_HISTORY_RETENTION_DAYS)
            
            # Условие для комнаты (обычная логика или только приватные/мои сообщения)
            if filter_only_me_and_my:
                room_condition = or_(
                    and_(
                        Message.room == "private",
                        or_(
                            func.array_position(Message.target_user_ids, character_id) != None,
                            Message.sender_id == character_id
                        )
                    ),
                    and_(
                        Message.room == room,
                        or_(
                            func.array_position(Message.target_user_ids, character_id) != None,
                            Message.sender_id == character_id
                        )
                    ),
                )
            else:
                room_condition = or_(
                    Message.room == room,
                    and_(
                        Message.room == "private",
                        or_(
                            func.array_position(Message.target_user_ids, character_id) != None,
                            Message.sender_id == character_id
                        )
                    )
                )
            
            base_conditions.append(room_condition)

            # Фильтр по игнорируемым персонажам
            if ignored_set:
                base_conditions.append(
                    or_(
                        Message.sender_id.notin_(ignored_set),
                        Message.sender_id.is_(None)
                    )
                )

            # Фильтр по торговым сообщениям
            trade_condition = or_(
                Message.is_trade == False,
                and_(Message.is_trade == True, sa.literal(show_trade_messages))
            )
            base_conditions.append(trade_condition)

            # Условие для location_slug
            if location_slug and show_location_messages and room == "global":
                location_base_conditions = []

                if filter_only_me_and_my:
                    location_room_condition = and_(
                        Message.room == location_slug,
                        or_(
                            func.array_position(Message.target_user_ids, character_id) != None,
                            Message.sender_id == character_id
                        )
                    )
                else:
                    location_room_condition = Message.room == location_slug
                
                location_base_conditions.append(location_room_condition)

                if ignored_set:
                    location_base_conditions.append(
                        or_(
                            Message.sender_id.notin_(ignored_set),
                            Message.sender_id.is_(None)
                        )
                    )

                location_trade_condition = or_(
                    Message.is_trade == False,
                    and_(Message.is_trade == True, sa.literal(show_trade_messages))
                )
                location_base_conditions.append(location_trade_condition)

                location_condition = and_(*location_base_conditions)
                base_conditions[0] = or_(location_condition, base_conditions[0])

            non_system_condition = and_(*base_conditions, Message.room != "system")

            # Запрос для не системных сообщений (100 штук) изменено на 75
            non_system_query = sa.select(Message).where(
                non_system_condition,
                Message.created_at >= cutoff,
            ).order_by(sa.desc(Message.created_at)).limit(75)

            non_system_result = await session.execute(non_system_query)
            non_system_messages = list(non_system_result.scalars().all())

            # Условия для системных сообщений
            system_messages = []
            if show_system_messages:
                system_condition = or_(
                    and_(
                        Message.room == "system",
                        Message.target_user_ids.is_(None),
                        Message.message_type != "SYSTEM_PRIVATE",
                        Message.message_type != "SYSTEM_PLAY_CHARACTER",
                    ),
                    and_(
                        Message.room == "system",
                        func.array_position(Message.target_user_ids, character_id) != None
                    )
                )
                
                # Запрос для системных сообщений (50 штук)
                system_query = sa.select(Message).where(
                    system_condition,
                    Message.created_at >= cutoff,
                ).order_by(sa.desc(Message.created_at)).limit(50)

                system_result = await session.execute(system_query)
                system_messages = list(system_result.scalars().all())

            # Объединяем сообщения и сортируем по времени
            all_messages = non_system_messages + system_messages
            all_messages.sort(key=lambda msg: msg.created_at, reverse=True)
            
            # Общее количество - это количество полученных сообщений
            total_count = len(all_messages)
            
            # Реверсируем для правильного порядка (от старых к новым)
            all_messages.reverse()

            # Преобразуем в схемы
            message_schemas = [MessageReadSchema.model_validate(msg, from_attributes=True) for msg in all_messages]

            return MessagePaginationReadSchema(
                objects=message_schemas,
                count=total_count
            )

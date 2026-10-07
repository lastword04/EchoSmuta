#!/usr/bin/env python3
"""
Скрипт для добавления всех предметов персонажу по одной штуке.

Использование:
    python add_all_items_to_character.py <character_id>

Пример:
    python add_all_items_to_character.py 999da4f0-7cf7-4925-a9aa-22956d1650b4
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent))

from mining_app.core.db import get_async_session
from mining_app.apps.items.repositories.character.character_items import CharacterItemRepository
from mining_app.apps.items.repositories.items.items import ItemRepository
from mining_app.apps.items.schemas import InventoryItemCreateSchema


async def add_all_items_to_character(character_id: uuid.UUID):
    """
    Добавляет все предметы из таблицы items персонажу по одной штуке.
    
    Args:
        character_id: UUID персонажа
    """
    print(f"Начинаем добавление всех предметов персонажу {character_id}...")
    
    # Получаем сессию
    session_gen = get_async_session()
    session = await anext(session_gen)
    
    try:
        # Создаём репозитории
        item_repository = ItemRepository(session)
        character_item_repository = CharacterItemRepository(session)
        
        # Получаем все предметы
        print("Получаем список всех предметов...")
        all_items = await item_repository.get_all()
        print(f"Найдено {len(all_items)} предметов")
        
        # Добавляем каждый предмет персонажу
        added_count = 0
        failed_count = 0
        
        for item in all_items:
            try:
                # Создаём данные для добавления предмета
                item_data = InventoryItemCreateSchema(
                    item_slug=item.slug,
                    amount=1,  # По одной штуке
                    expired_date=None,  # Без срока годности
                    used_count=0 if item.parameters and 'max_used' in item.parameters else None,
                    wear=0 if item.parameters and 'max_wear' in item.parameters else None
                )
                
                # Добавляем предмет
                await character_item_repository.add_item(character_id, item_data)
                added_count += 1
                print(f"✓ Добавлен: {item.name} ({item.slug})")
                
            except Exception as e:
                failed_count += 1
                print(f"✗ Ошибка при добавлении {item.name} ({item.slug}): {e}")
        
        print(f"\n{'='*60}")
        print(f"Завершено!")
        print(f"Успешно добавлено: {added_count}")
        print(f"Ошибок: {failed_count}")
        print(f"Всего предметов: {len(all_items)}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise
    finally:
        # Закрываем сессию
        await session.close()


async def main():
    """Главная функция скрипта."""
    if len(sys.argv) != 2:
        print("Использование: python add_all_items_to_character.py <character_id>")
        print("Пример: python add_all_items_to_character.py 999da4f0-7cf7-4925-a9aa-22956d1650b4")
        sys.exit(1)
    
    try:
        character_id = uuid.UUID(sys.argv[1])
    except ValueError:
        print(f"Ошибка: '{sys.argv[1]}' не является валидным UUID")
        sys.exit(1)
    
    await add_all_items_to_character(character_id)


if __name__ == "__main__":
    asyncio.run(main())

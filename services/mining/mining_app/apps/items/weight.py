# ============================================================
# Пересчёт веса персонажа после изменений инвентаря
# ============================================================

async def recalculate_character_weight(inventory_service, characters_client, character_id) -> None:
    """
    Пересчитывает суммарный вес предметов и отправляет в characters-сервис.
    При ошибке НЕ роняет основную операцию — только логирует.
    """
    try:
        total = await inventory_service.get_total_weight(character_id)
        await characters_client.update_weight(character_id, float(total))
    except Exception as e:
        print(f"[weight] recalc failed for {character_id}: {e}")
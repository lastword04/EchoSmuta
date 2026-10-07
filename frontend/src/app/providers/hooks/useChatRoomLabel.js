import { useSelector } from 'react-redux';
import { useGetHousesStatusQuery } from '../../../entities/character/api/housesApi';

export const useChatRoomLabel = (character) => {
    // ИСТИНА: Мы внутри дома, если chat_room_id указывает на дом.
    // Это самый стабильный индикатор, он не затирается applySnapshot.
    const isInsideHouse = character?.chat_room_id?.startsWith('house:');
    
    // Фоллбэк на случай, если chat_room_id еще не проставлен, но current_house_id есть
    const hasHouseFallback = !!character?.current_house_id;
    
    const houseOverride = useSelector(state => state.houseUi?.houseOverride ?? null);
    
    // ID дома для поиска: приоритет у override, затем current_house_id
    const targetHouseId = houseOverride?.id ?? character?.current_house_id;

    const { data: housesData } = useGetHousesStatusQuery(character?.id, {
        skip: !character?.id || (!isInsideHouse && !hasHouseFallback),
    });

    if (!isInsideHouse && !hasHouseFallback) return null;

    // 1. Приоритет: оптимистичный override (если он совпадает с targetHouseId)
    if (houseOverride && targetHouseId && houseOverride.id === targetHouseId) {
        return `Дом №${houseOverride.number}`;
    }

    // 2. АТОМАРНОСТЬ: Если данные еще грузятся, возвращаем null.
    if (!housesData) return null;

    // 3. Данные загружены. Ищем дом.
    // Если targetHouseId есть, ищем по нему. Иначе берем current_house из ответа бэка.
    const house = targetHouseId
        ? (housesData.houses?.find(h => h.id === targetHouseId) || (housesData.current_house?.id === targetHouseId ? housesData.current_house : null))
        : housesData.current_house;

    return house ? `Дом №${house.number}` : null;
};
import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { moveOnlineUser, setOnlineUserPresence } from '../lib/onlineCacheSync';

/**
 * Синхронизация RTK Query-кэшей онлайна с presence-событиями от WebSocket.
 * 
 * Подключается один раз в withBasePage (корень приложения) и живёт всё время
 * жизни сессии. После первичного REST-снапшота — единственный источник
 * live-обновлений для списка онлайн: никаких polling/refetch, только updateQueryData.
 *
 * Игнорирует события о самом персонаже — их обрабатывает useLocationTransition
 * оптимистично, в один тик с commitLocation (иначе были бы промежуточные кадры
 * между presence и сменой character.location_slug в UI).
 *
 * Единый WebSocket (ChatWebSocketProvider) мультиплексирует все события,
 * поэтому presence-события приходят ровно один раз — дедупликация не нужна.
 */


export const usePresenceSync = () => {
    const dispatch = useDispatch();
    const myCharacterId = useSelector(state => state.local.activeCharacterId);

    // Ref для актуального ID в обработчике — listener не пересоздаётся при смене персонажа,
    // но всегда видит актуальное значение (защита от race condition при SPA-логауте)
    const myCharacterIdRef = useRef(myCharacterId);
    useEffect(() => {
        myCharacterIdRef.current = myCharacterId;
    }, [myCharacterId]);

    useEffect(() => {
        const handleCharacterOnline = ({ character_id, is_online, location_slug: eventLocationSlug, user_data }) => {
            setOnlineUserPresence(dispatch, {
                characterId: character_id,
                isOnline: is_online,
                locationSlug: eventLocationSlug,
                userData: user_data
            });
        };

        const handleCharacterLocation = ({
            character_id,
            old_location_slug,
            new_location_slug,
            old_real_location_slug,
            new_real_location_slug,
            user_data,
        }) => {
            if (!user_data) return;

            moveOnlineUser(dispatch, {
                characterId: character_id,
                oldLocationSlug: old_location_slug,
                newLocationSlug: new_location_slug,
                oldRealLocationSlug: old_real_location_slug,
                newRealLocationSlug: new_real_location_slug,
                userData: user_data,
            });
        };

        const handlePresenceEvent = (event) => {            
            const {
                event_type, character_id, user_data,
                old_location_slug, new_location_slug,
                old_real_location_slug, new_real_location_slug,
                is_online, location_slug: eventLocationSlug
            } = event.detail;

            if (character_id === myCharacterIdRef.current) return;

            if (event_type === 'character_online') {
                handleCharacterOnline({ character_id, is_online, location_slug: eventLocationSlug, user_data });
            } else if (event_type === 'character_location') {
                handleCharacterLocation({
                    character_id,
                    old_location_slug,
                    new_location_slug,
                    old_real_location_slug,
                    new_real_location_slug,
                    user_data,
                });
            }
        };

        // Фильтр своих событий есть выше: character_id === myCharacterIdRef.current (ref — listener не пересоздаётся)
        // eslint-disable-next-line no-restricted-syntax
        window.addEventListener('presence-event', handlePresenceEvent);
        return () => {
            window.removeEventListener('presence-event', handlePresenceEvent);
        };
    }, [dispatch]);
};
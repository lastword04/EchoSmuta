import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addToOfflineQueue, flushOfflineQueue } from '../../../entities/chat/lib/offlineQueue';
import { ChatWebSocket } from '../../../shared/lib/websocket/ChatWebSocket';
import { useGetMySettingsQuery } from '../../../entities/chat/api/chatApi';
import { routeMessageToCaches } from '../../../entities/chat/lib/messageRouter';
import { useErrorContext } from '../../../shared/lib/context/ErrorContext';
import { ChatWebSocketContext } from '../../../shared/lib/context/ChatWebSocketContext';

/**
 * Единый WebSocket на всю сессию (Вариант A).
 * 
 * Один экземпляр ChatWebSocket подключается к room='global' и живёт всё время
 * жизни сессии. Мультиплексирует: presence, чат (global/location/private),
 * почта, экономика, крафт — всё через одно соединение.
 * 
 * Сервер сам переподписывает локационные каналы при character_location
 * (см. WebSocketManager.listen_to_room), поэтому пересоздавать сокет
 * при смене локации НЕ нужно.
 * 
 * При send автоматически добавляется room в payload (текущая активная вкладка
 * чата) — для серверного мультиплексирования.
 */
export const ChatWebSocketProvider = ({ character, children }) => {
    const dispatch = useDispatch();
    const { showError } = useErrorContext();
    const activeTab = useSelector((state) => state.session.activeTab);

    const wsRef = useRef(null);
    const sendRef = useRef(() => false);
    const audioRef = useRef({ general: null, privateMsg: null });
    const characterRef = useRef(character);
    const activeTabRef = useRef(activeTab);

    // Settings: свой запрос с дедупликацией через RTK Query кэш
    const { data: settings } = useGetMySettingsQuery(undefined, { 
        skip: !character?.id 
    });
    const settingsRef = useRef(settings);

    // Sync refs (чтобы handler всегда видел актуальные значения без пересоздания сокета)
    useEffect(() => {
        characterRef.current = character;
    }, [character]);

    useEffect(() => {
        activeTabRef.current = activeTab;
    }, [activeTab]);

    useEffect(() => {
        settingsRef.current = settings;
    }, [settings]);

    // Аудио (один раз на сессию)
    useEffect(() => {
        audioRef.current.general = new Audio('/sounds/GeneralChat.mp3');
        audioRef.current.privateMsg = new Audio('/sounds/PrivateChat.mp3');
    }, []);

    // Сокет: создаётся всегда когда есть character.id.
    // settings?.chat_enabled влияет только на UI чата (не на инфраструктуру сокета).
    // Пересоздаётся ТОЛЬКО при смене character.id (новый токен/персонаж).
    useEffect(() => {
        if (!character?.id) {
            if (wsRef.current) {
                wsRef.current.disconnect();
                wsRef.current = null;
                sendRef.current = () => false;
            }
            return;
        }

        const play = (audio) => {
            if (audio) {
                audio.currentTime = 0;
                audio.play().catch(() => {});
            }
        };

        const onMessage = (message) => {                  
            const currentSettings = settingsRef.current;
            const currentChar = characterRef.current;
            if (!currentChar) return;

            // Ошибки от сервера (rate limit, validation, etc.)
            // Ошибки от сервера (rate limit, validation, etc.)
            if (message && (message.error_code || message.error_type || message.detail)) {
                const text =
                    message.error_code === 'RATE_LIMIT_EXCEEDED'
                        ? 'Пожалуйста, не пишите так часто.'
                        : message.detail || 'Произошла ошибка';    
                showError(text);    
                return;
            }
            
            // Если settings не загрузились — не маршрутизируем сообщения
            if (!currentSettings) return;      

            // Звуки: играем ТОЛЬКО когда мы — адресат сообщения.
            // Тип звука по комнате: private → приватный, иначе → общий.
            // Сообщения без адресата и чужие переписки — тишина.
            if (message.sender_id !== currentChar.id) {
                const isForMe = (message.target_user_ids || []).includes(currentChar.id);
                if (isForMe) {
                    if (message.room === 'private' && currentSettings.sound_private_message) {
                        play(audioRef.current.privateMsg);
                    } else if (message.room !== 'private' && currentSettings.sound_general_chat) {
                        play(audioRef.current.general);
                    }
                }
            }

            try {
                routeMessageToCaches(dispatch, {
                    message,
                    character: currentChar,
                    settings: currentSettings,
                });
            } catch (err) {
                console.error('Ошибка роутинга сообщения чата:', err);
            }
        };

        // room='global' — сервер сам подписывает на актуальный канал
        // (локационный или виртуальный, 'house:uuid' / 'inn:inside'),
        // переподписывается на character_location.
        wsRef.current = new ChatWebSocket(
            'global',
            character.chat_room_id ?? character.location_slug,
            onMessage,
            (error) => console.error('WebSocket error:', error),
            undefined,
            // Ресинк экономики после реконнекта: события, ушедшие в обрыв,
            // потеряны (pub/sub без истории) — инвалидации через то же
            // событийное окно, что и обычные economy-события.
            () => window.dispatchEvent(new CustomEvent('economy-resync')),
        );
        wsRef.current.connect();
        

        sendRef.current = (payload) => {
            if (wsRef.current && wsRef.current.isConnected()) {
                const currentTab = activeTabRef.current;
                const currentChar = characterRef.current;
                const targetRoom = currentTab === 'Локация' 
                    ? (currentChar?.chat_room_id ?? currentChar?.location_slug)
                    : 'global';

                wsRef.current.send({
                    ...payload,
                    room: targetRoom,
                });
                return true;
            }
            // Нет соединения — сохраняем в очередь
            addToOfflineQueue(payload);
            return false;
        };

        // Проверяем очередь при подключении
        const queuedMessages = flushOfflineQueue();
        queuedMessages.forEach(msg => sendRef.current(msg));

        return () => {
            if (wsRef.current) {
                wsRef.current.disconnect();
                wsRef.current = null;
                sendRef.current = () => false;
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [character?.id]); // ← УБРАЛИ settings?.chat_enabled из зависимостей

    return (
        <ChatWebSocketContext.Provider value={sendRef.current}>
            {children}
        </ChatWebSocketContext.Provider>
    );
};

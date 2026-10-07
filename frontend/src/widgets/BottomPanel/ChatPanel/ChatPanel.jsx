import { useEffect, useState, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { invalidateChatCache } from '../../../entities/chat/lib/cacheInvalidation';

import { useErrorContext } from '../../../shared/lib/context/ErrorContext';
import { chatApi, chatHistoryArgs, useGetMySettingsQuery, useGetChatHistoryQuery } from '../../../entities/chat/api/chatApi';
import { useChatSend } from '../../../entities/chat/hooks/useChatSend';

import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { ChatSettings } from './ChatSettings/ChatSettings';
import BellsPanel from './BellsPanel/BellsPanel';
import ChatContent from './ChatContent/ChatContent';
import { fetchBellMapCached } from '../../../entities/chat/lib/bellsData';
import ChatInput from './ChatInput/ChatInput';
import { debounce } from '../../../shared/lib/utils/debounce';

import styles from './ChatPanel.module.css';



/**
 * Вычисление ключа комнаты для инвалидации кэша
 */
const computeRoomKey = (room, roomId, filterLocation) => {
    if (room === 'global' && filterLocation && roomId) {
        return `location:${roomId}`;
    }
    return room;
};

/**
 * Прогрев кэша картинок: создаёт Image() для каждого смайлика из сообщений,
 * чтобы браузер загрузил и декодировал гифки ДО того, как пользователь
 * переключит вкладку и увидит их в DOM.
 */
const smileyCodeRegex = /\|(\d+)\|/g;
const preloadSmileys = async (messagesList) => {
    if (!messagesList?.length) return;
    try {
        const bellMap = await fetchBellMapCached();
        const codes = new Set();
        messagesList.forEach((msg) => {
            const text = msg.text || '';
            smileyCodeRegex.lastIndex = 0;
            let match;
            while ((match = smileyCodeRegex.exec(text)) !== null) {
                codes.add(match[1]);
            }
        });
        codes.forEach((code) => {
            const img = new Image();
            img.src = `/images/bells/${bellMap[code] || 'Emotions'}/${code}.gif`;
        });
    } catch {
        // Прелоад не критичен — молча пропускаем
    }
};


export const ChatPanel = ({ activeChatRoom, roomId }) => {
    const dispatch = useDispatch();    
    const { currentError, showError } = useErrorContext();

    // --- State ---
    const [settings, setSettings] = useState(null);  
    const [settingsLoaded, setSettingsLoaded] = useState(false);  
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isTradeMode, setIsTradeMode] = useState(false);
    const [isBellsOpen, setIsBellsOpen] = useState(false);
    const [selectedCharacters, setSelectedCharacters] = useState([]); 
    const [inputValue, setInputValue] = useState('');

    // --- RTK Query ---
    const { data: settingsData, isLoading: isSettingsLoading, isError: isSettingsError } = useGetMySettingsQuery();
    
    const locationForHistory = settings?.filter_location_messages ? roomId : null;
    const args = chatHistoryArgs(activeChatRoom, locationForHistory);
    const { 
        data: messages = [],         
    } = useGetChatHistoryQuery(
        args,
        { 
            skip: !settingsLoaded || !settings?.chat_enabled || !activeChatRoom,
        }
    );

    // --- WebSocket ---
    // Единый сокет из ChatWebSocketProvider (room='global', сервер мультиплексирует)
    // room в payload добавляется автоматически на основе activeTab
    const send = useChatSend();

    // --- Sync settings from RTK Query ---
    useEffect(() => {
        if (settingsData && !isSettingsLoading) {
            setSettings(settingsData);
            setSettingsLoaded(true);
        }
        if (isSettingsError) {
            showError('Не удалось загрузить настройки чата');
        }
    }, [settingsData, isSettingsLoading, isSettingsError, showError]);

    // --- Prefetch history for both tabs (instant switching) ---
    useEffect(() => {
        if (!settingsLoaded || !settings?.chat_enabled) return;

        const location = settings?.filter_location_messages ? roomId : null;

        // Prefetch ОБЕИХ комбинаций locationSlug для обеих комнат:
        // иначе при переключении вкладки args могут не совпасть с prefetch
        // и RTK Query сделает новый запрос → мелькание пустого списка
        const combos = [
            chatHistoryArgs('global', location),
        ];
        if (roomId) {
            combos.push(chatHistoryArgs(roomId, location));
        }

        combos.forEach((args) => {
            dispatch(
                chatApi.endpoints.getChatHistory.initiate(
                    args,
                    { subscribe: false }
                )
            ).then(({ data }) => preloadSmileys(data));
        });
    }, [settingsLoaded, settings?.chat_enabled, settings?.filter_location_messages, roomId, dispatch]);

    // --- Handle smiley clicks ---
    useEffect(() => {
        const handleSmileyClick = (e) => {
            setInputValue(prev => prev + e.detail.smileyCode);
        };

        window.addEventListener('smileyClick', handleSmileyClick);
        return () => window.removeEventListener('smileyClick', handleSmileyClick);
    }, []);

    // --- Handle refresh chat event ---
    useEffect(() => {
        const handleRefreshChat = (event) => {
            if (!settingsLoaded || !settings?.chat_enabled) return;
            try {
                const { tab, roomId: eventRoomId } = event.detail;
                const room = tab === 'Локация' ? eventRoomId : 'global';
                const roomKey = computeRoomKey(room, eventRoomId, settings?.filter_location_messages);
                
                invalidateChatCache(dispatch, { history: true, historyRoom: roomKey });
            } catch (error) {
                console.error('Ошибка при обновлении истории чата:', error);
                showError('Не удалось обновить историю чата');
            }
        };

        const debouncedHandler = debounce(handleRefreshChat, 300);

        window.addEventListener('refreshChat', debouncedHandler);
        return () => window.removeEventListener('refreshChat', debouncedHandler);
    }, [settingsLoaded, settings?.chat_enabled, settings?.filter_location_messages, dispatch, showError]);

    // --- Character selection handlers ---
    const handleCharacterSelect = useCallback((name, id, isPrivate = false) => {
        setIsTradeMode(false);

        setSelectedCharacters(prev => {
            const existsIndex = prev.findIndex(c => c.id === id);
            const isAlreadySelected = existsIndex !== -1;

            if (isAlreadySelected) {
                const exists = prev[existsIndex];
                const newPrivateState = !exists.isPrivate;
                return prev.map(c => ({ ...c, isPrivate: newPrivateState }));
            }

            let newList = [...prev, { name, id, isPrivate }];
            const anyPrivate = newList.some(c => c.isPrivate);
            if (anyPrivate) {
                newList = newList.map(c => ({ ...c, isPrivate: true }));
            }

            return newList;
        });
    }, []);

    const handleCharacterUnselect = useCallback((characterId) => {
        setSelectedCharacters(prev => {
            const updated = prev.filter(c => c.id !== characterId);
            if (updated.length > 0) {
                const anyPrivate = updated.some(c => c.isPrivate);
                return updated.map(c => ({ ...c, isPrivate: anyPrivate }));
            }
            return updated;
        });
    }, []);

    const handleTradeToggle = useCallback((value) => {
        if (value && selectedCharacters.length > 0) return;

        setIsTradeMode(value);
        if (value) setSelectedCharacters([]);
    }, [selectedCharacters.length]);

    // --- Handle character selection from external sources ---
    useEffect(() => {
        const handleCharacterSelectEvent = (event) => {
            const { name, id, isPrivate = false } = event.detail;
            handleCharacterSelect(name, id, isPrivate);
        };

        window.addEventListener('characterSelected', handleCharacterSelectEvent);
        return () => window.removeEventListener('characterSelected', handleCharacterSelectEvent);
    }, [handleCharacterSelect]);

    // --- Clear chat ---
    const handleClearChat = useCallback(() => {
        const location = settings?.filter_location_messages ? roomId : null;
        
        dispatch(
            chatApi.util.updateQueryData(
                'getChatHistory',
                chatHistoryArgs(activeChatRoom, location),
                (draft) => {
                    draft.length = 0; // Очищаем массив сообщений
                }
            )
        );
    }, [activeChatRoom, roomId, settings?.filter_location_messages, dispatch]);

    // --- Send message ---
    const handleSendMessage = useCallback((messageText, isPrivate = false, targetUserIds = [], isTrade = false) => {
        if (!settings?.chat_enabled) {
            showError('Чат отключён');
            return;
        }

        const sent = send({
            content: messageText,
            is_private: isPrivate,
            is_trade: isTrade,
            ...(targetUserIds.length > 0 && { target_user_ids: targetUserIds }),
        });

        if (!sent) {
            showError('Нет соединения с чатом');
        }
    }, [settings?.chat_enabled, send, showError]);

    const handleSendMessageAndClear = useCallback((messageText) => {
        if (isBellsOpen) setIsBellsOpen(false);
        
        const privateRecipients = selectedCharacters.filter(char => char.isPrivate);
        const mentions = selectedCharacters.filter(char => !char.isPrivate);

        let finalContent = messageText;
        let targetUserIds = [];
        let isPrivate = false;
        let isTrade = isTradeMode;

        if (privateRecipients.length > 0) {
            isPrivate = true;
            targetUserIds = privateRecipients.map(c => c.id);
        } else if (mentions.length > 0) {
            targetUserIds = mentions.map(c => c.id);
        }

        handleSendMessage(finalContent, isPrivate, targetUserIds, isTrade);
        setSelectedCharacters([]);
        setIsTradeMode(false);
    }, [isBellsOpen, selectedCharacters, isTradeMode, handleSendMessage]);

    // --- Settings reload handler ---
    const handleSettingsReload = useCallback((action) => {
        if (action === 'reload') {
            invalidateChatCache(dispatch, { history: true });
        } else if (action === 'clear') {
            handleClearChat();
        }
    }, [dispatch, handleClearChat]);

    if (!settings) return null;

    return (
        <div className={styles.chatPanel}>
            <ErrorToast message={currentError} variant="chat" />
            {isSettingsOpen ? (
                <ChatSettings
                    settings={settings}
                    onUpdate={setSettings}                    
                    onSettingsReload={handleSettingsReload}
                    dispatch={dispatch}
                />
            ) : isBellsOpen ? (
                <BellsPanel
                    onBellSelect={(bellCode) => setInputValue(prev => prev + bellCode)}                    
                />
            ) : (
                <ChatContent                    
                    settings={settings}
                    messages={messages}
                    onCharacterClick={handleCharacterSelect}
                    currentUserId={settings.character_id}
                    roomId={roomId}
                />
            )}

            {(selectedCharacters.length > 0 || isTradeMode) && (
                <div className={styles.characterTabsContainer}>
                    {selectedCharacters.map((character) => (
                        <div
                            key={character.id}
                            className={`${styles.characterTab} ${character.isPrivate ? styles.privateTab : ''}`}
                        >
                            <span
                                className={styles.characterTabText}
                                onClick={() => handleCharacterSelect(character.name, character.id, character.isPrivate)}
                                title={
                                    character.isPrivate
                                        ? 'Кликните для возврата к упоминанию'
                                        : 'Кликните для отправки приватного сообщения'
                                }
                            >
                                {character.name}
                            </span>
                            <button
                                className={styles.characterTabClose}
                                onClick={() => handleCharacterUnselect(character.id)}
                            >
                                ×
                            </button>
                        </div>
                    ))}

                    {isTradeMode && (
                        <div className={`${styles.characterTab} ${styles.tradeTab}`}>
                            <span className={styles.characterTabText}>Торговля</span>
                            <button
                                className={styles.characterTabClose}
                                onClick={() => setIsTradeMode(false)}
                            >
                                ×
                            </button>
                        </div>
                    )}
                </div>
            )}

            <ChatInput
                settings={settings}
                onSettingsToggle={() => {
                    setIsSettingsOpen(!isSettingsOpen);
                    setIsBellsOpen(false);
                }}
                onSendMessage={handleSendMessageAndClear}
                selectedCharacters={selectedCharacters}
                isTradeMode={isTradeMode}
                onTradeToggle={handleTradeToggle}
                onClearChat={handleClearChat}
                onShowBells={() => {
                    setIsBellsOpen(!isBellsOpen);
                    setIsSettingsOpen(false);
                }}
                setInputValue={setInputValue}
                inputValue={inputValue}
            />
        </div>
    );
};

export default ChatPanel;
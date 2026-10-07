import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';
import { getLocationName } from '../../../shared/config/locations/locations';
import {
    useAddToIgnoreMutation,
    useDeleteFromIgnoreMutation,
    useGetOnlineCharactersQuery,
    chatApi
} from '../../../entities/chat/api/chatApi';
import { setActiveTab } from '../../../shared/store/activeTabSlice';
import { debounce } from '../../../shared/lib/utils/debounce';

import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { UserListItem } from './UserListItem';
import styles from './UserListPanel.module.css';



export const UserListPanel = ({
    roomId,
    roomLabel,
    character_id,
    character_level,
    character_name
}) => {
    // --- Hooks ---
    const dispatch = useDispatch();
    const activeTab = useSelector((state) => state.session.activeTab);

    // --- RTK Query mutations ---
    const [addToIgnore] = useAddToIgnoreMutation();
    const [deleteFromIgnore] = useDeleteFromIgnoreMutation();

    // --- RTK Query subscriptions ---
    // Единственный запрос — глобальный список онлайн. Список для комнаты
    // фильтруется локально из него. Это даёт атомарное переключение при
    // смене roomId: список и count пересчитываются в одном рендере.
    // Раньше был отдельный запрос по {roomId}, из-за чего count и список
    // отставали на один-два кадра от заголовка.
    const { data: globalData } = useGetOnlineCharactersQuery({
        locationSlug: null,
        limit: 50,
        offset: 0,
    });

    // --- State ---    
    const [ignorePendingId, setIgnorePendingId] = useState(null);

    // --- Refs ---
    const userListRef = useRef(null);
    const stateRef = useRef({ activeTab, roomId });
    const scrollStateRef = useRef({
        hasScrolled: false,
        lastScrollTop: 0,
        hideTimeout: null,
        isScrolling: false,
        programmaticScroll: false,
    });

    // --- Derived values ---
    const globalObjects = globalData?.objects || [];
    const currentUsers = useMemo(() => {
        if (activeTab === 'Общий') return globalObjects;
        if (!roomId) return [];
        // Фильтр по «актуальному пространству» персонажа:
        //   - если он в виртуальной комнате (дом/номер) → current_room_id
        //   - иначе → location_slug (обычная локация)
        // Так работает и после F5 внутри дома: бэк возвращает current_room_id
        // из БД, фильтр находит игрока без дополнительной локальной синхронизации.
        return globalObjects.filter(u => (u.current_room_id ?? u.location_slug) === roomId);
    }, [activeTab, globalObjects, roomId]);
    const currentUserListCount = currentUsers.length;
    const showTitles = useMemo(() => character_level < 2, [character_level]);

    const { currentError, showError } = useErrorToast();

    // --- Sync state to ref for use in callbacks ---
    useEffect(() => {
        stateRef.current = { activeTab, roomId };
    }, [activeTab, roomId]);

   

    // --- UI handlers ---
    
    // debounce вызывается один раз при монтировании (useCallback кэширует обёртку),
    // внутри замыкания только dispatch (стабилен) — exhaustive-deps не может
    // заглянуть в debounce и ругается "unknown dependencies"
    // eslint-disable-next-line react-hooks/exhaustive-deps
    const handleTabClick = useCallback(
        debounce((tab) => {
            dispatch(setActiveTab(tab));
        }, 300),
        [dispatch]
    );

    const handleSearch = useCallback(() => {
        window.open(`/characters/search?q=${character_name}`, '_blank');
    }, [character_name]);

    const handleNavigate = useCallback((id) => {
        window.open(`/characters/${id}`, '_blank');
    }, []);

    const toggleIgnore = useCallback(async (user) => {
        // Блокировка: если по этому юзеру уже летит мутация — игнорируем клик
        if (ignorePendingId === user.id) return;
        
        const isIgnored = user.is_ignored;
        setIgnorePendingId(user.id);
        
        try {
            // Выполняем мутацию на сервере
            if (isIgnored) {
                await deleteFromIgnore(user.id).unwrap();
            } else {
                await addToIgnore({ ignored_character_id: user.id }).unwrap();
            }
            
            // Мгновенно обновляем кэш (без refetch)
            const newIsIgnored = !isIgnored;
            dispatch(
                chatApi.util.updateQueryData(
                    'getOnlineCharacters',
                    { locationSlug: null, limit: 50, offset: 0 },
                    (draft) => {
                        const idx = draft.objects?.findIndex(u => u.id === user.id);
                        if (idx !== undefined && idx !== -1) {
                            draft.objects[idx].is_ignored = newIsIgnored;
                        }
                    }
                )
            );           
            
            // Инвалидация для синхронизации с сервером (в фоне)
            dispatch(
                chatApi.util.invalidateTags([
                    { type: 'OnlineUsers', id: 'global' },
                    'ChatHistory',
                ])
            );
        } catch (error) {
            // Обработка ошибок
            const isCooldownError = error?.data?.error_code === "IGNORE_COOLDOWN_ERROR";
            if (isCooldownError) {
                const coolDownTime = error?.data?.extras?.remaining_time;
                showError(`Не прошёл кд, повторите через ${Math.ceil(coolDownTime)} секунд`);
            } else {
                const detail = error?.data?.detail || error?.message || 'Неизвестная ошибка';
                showError(detail);
            }
        } finally {
            setIgnorePendingId(null);
        }
    }, [roomId, showError, dispatch, addToIgnore, deleteFromIgnore, ignorePendingId]);

    const handleUserLinkClick = useCallback((user) => {
        window.dispatchEvent(new CustomEvent('characterSelected', {
            detail: { name: user.name, id: user.id, isPrivate: false }
        }));
    }, []);

    const handlePrivateClick = useCallback((user) => {
        window.dispatchEvent(new CustomEvent('characterSelected', {
            detail: { name: user.name, id: user.id, isPrivate: true }
        }));
    }, []);

    // --- Scrollbar visibility management ---
    useEffect(() => {
        const list = userListRef.current;
        if (!list) return;

        // Guard: не даём setTimeout мутировать DOM после unmount
        let isCleanedUp = false;

        list.style.setProperty('--show-scroll', '1');

        const data = scrollStateRef.current;
        
        if (data.lastScrollTop === 0) {
            data.hasScrolled = false;
            data.lastScrollTop = list.scrollTop;
            data.hideTimeout = null;
            data.isScrolling = false;
            data.programmaticScroll = false;
        }

        const showScrollbar = () => {
            list.style.setProperty('--show-scroll', '1');
            if (data.hideTimeout) {
                clearTimeout(data.hideTimeout);
                data.hideTimeout = null;
            }
        };

        const hideScrollbarWithDelay = () => {
            if (data.hideTimeout) clearTimeout(data.hideTimeout);
            data.hideTimeout = setTimeout(() => {
                if (isCleanedUp) return;
                list.style.setProperty('--show-scroll', '0');
                data.isScrolling = false;
            }, 1000);
        };

        const handleScroll = () => {
            const currentScrollTop = list.scrollTop;

            if (currentScrollTop !== data.lastScrollTop) {
                if (data.programmaticScroll) {
                    data.programmaticScroll = false;
                    data.lastScrollTop = currentScrollTop;
                    return;
                }

                if (!data.isScrolling) {
                    showScrollbar();
                    data.isScrolling = true;
                }

                data.hasScrolled = true;
                data.lastScrollTop = currentScrollTop;
            }

            if (data.hasScrolled) hideScrollbarWithDelay();
        };

        const handleMouseMove = (e) => {
            const rect = list.getBoundingClientRect();
            const scrollbarWidth = list.offsetWidth - list.clientWidth;

            if (e.clientX >= rect.right - scrollbarWidth) {
                showScrollbar();
            } else if (!data.isScrolling) {
                hideScrollbarWithDelay();
            }
        };

        list.addEventListener('scroll', handleScroll, { passive: true });
        list.addEventListener('mousemove', handleMouseMove);

        return () => {
            isCleanedUp = true;
            list.removeEventListener('scroll', handleScroll);
            list.removeEventListener('mousemove', handleMouseMove);
            if (data.hideTimeout) {
                clearTimeout(data.hideTimeout);
                data.hideTimeout = null;
            }
            list.style.removeProperty('--show-scroll');
        };
    }, [activeTab]);

    // --- Render ---
    return (
        <div className={styles.userListPanel}>
            <ErrorToast message={currentError} variant="chat" />
            <div className={styles.header}>
                <h3 className={styles.locationName}>
                    {roomId && currentUserListCount !== undefined
                        ? `${roomLabel || getLocationName(roomId)} (${currentUserListCount})`
                        : ''
                    }
                </h3>
                <div className={styles.tabs}>
                    <button
                        className={activeTab === 'Общий' ? styles.activeLink : styles.inactiveLink}
                        onClick={() => handleTabClick('Общий')}
                    >
                        Общий
                    </button>
                    <span className={styles.separator}>•</span>
                    <button
                        className={activeTab === 'Локация' ? styles.activeLink : styles.inactiveLink}
                        onClick={() => handleTabClick('Локация')}
                    >
                        Локация
                    </button>
                </div>

                <div className={styles.iconButtons}>
                    <img
                        src="/images/widgets/userlist-panel/search.png"
                        alt="Поиск"
                        className={styles.iconImg}
                        onClick={handleSearch}
                    />
                    <img
                        src="/images/widgets/userlist-panel/update.png"
                        alt="Обновить"
                        title="Обновить список и чат"
                        className={styles.iconImg}
                        onClick={() => {
                            dispatch(
                                chatApi.util.invalidateTags([
                                    { type: 'OnlineUsers', id: 'global' },
                                ])
                            );
                            window.dispatchEvent(new CustomEvent('refreshChat', {
                                detail: { tab: activeTab, roomId }
                            }));
                        }}
                    />
                    <img
                        src="/images/widgets/userlist-panel/forum.png"
                        alt="Форум"
                        className={styles.iconImg}
                        onClick={() => window.open(`/forum`, '_blank')}
                    />
                </div>
            </div>

            <div className={styles.userList} ref={userListRef}>
                {currentUsers.map((user, index) => (
                    <UserListItem
                        key={user.id}
                        user={user}
                        index={index}
                        isLastItem={false}                       
                        character_id={character_id}
                        showTitles={showTitles}
                        onToggleIgnore={toggleIgnore}
                        onPrivateClick={handlePrivateClick}
                        onUserLinkClick={handleUserLinkClick}
                        onNavigate={handleNavigate}
                        isIgnorePending={ignorePendingId === user.id}
                    />
                ))}

                
            </div>
        </div>
    );
};
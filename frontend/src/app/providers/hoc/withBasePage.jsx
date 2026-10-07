/**
 * withBasePage — HOC-оркестратор активной игровой сессии.
 *
 * Обеспечивает:
 *  - готовность страницы (useAtomicPageReady)
 *  - WebSocket-подключения (economy, presence, chat)
 *  - управление модалками и меню (useModalState)
 *  - переходы между локациями (useLocationTransition)
 *  - глобальное обновление данных (useBaseRefresh)
 *  - единый layout игры (TopBar + текущая страница + CharacterPanel + BottomPanel + Modals)
 *
 * Используется ТОЛЬКО для игровых страниц (слой pages), которые оборачиваются
 * в LocationContainer (app/locations).
 *
 * НЕ путать с `shared/hoc/BaseMainPage/withBaseMainPage.jsx` — тот является
 * презентационным HOC'ом для публичных страниц (Login, Register, Forum и т.д.).
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';

import { TopBar } from '../../../widgets/TopBar/TopBar';
import { BottomPanel } from '../../../widgets/BottomPanel/BottomPanel';
import { CharacterPanel } from '../../../widgets/CharacterPanel/CharacterPanel';

import { useBaseRefresh } from '../hooks/useBaseRefresh';
import { useCharacter } from '../../../entities/character/hooks/useCharacter';
import { ChatWebSocketProvider } from '../hooks/useGlobalWebSocket';
import { useMailNotifications } from '../../../entities/mail/hooks/useMailNotifications';
import { useCharacterSkills } from '../../../entities/character/hooks/useCharacterSkills';
import { useModalState } from '../hooks/useModalState';
import { useAtomicPageReady } from '../hooks/useAtomicPageReady';
import { useLocationTransition } from '../hooks/useLocationTransition';
import { useChatRoomLabel } from '../hooks/useChatRoomLabel';

import { resetNavigation } from '../../../shared/store/locationNavigationSlice';
import { selectRefreshing } from '../store/refreshSlice';
import { selectHasUnreadMessages } from '../../../entities/mail/store/mailSlice';
import { useLocationRegistry } from '../../../shared/lib/context/locationContext';
import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';
import { useEconomyWebSocket } from '../hooks/useEconomyWebSocket';
import { usePresenceSync } from '../hooks/usePresenceSync';

import { requestTradeAction } from '../../../shared/store/topBarActionsSlice';

import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { ErrorProvider } from '../../../shared/lib/context/ErrorContext';
import Modals from '../../shell/BaseModals';

import styles from './BasePage.module.css';

export function withBasePage() {
    return function BasePageWrapper({ ...pageProps }) {       
        const [panelHeight, setPanelHeight] = useState(30);    
        const [error] = useState(null);
        
        const dispatch = useDispatch();    
        const navigate = useNavigate();
        const { currentError, showError } = useErrorToast();    

        // useCharacter должен быть ПЕРВЫМ, потому что другие хуки принимают character
        const { character } = useCharacter();
        const chatRoomLabel = useChatRoomLabel(character);
        const getComponentForLocation = useLocationRegistry();

        // Global listeners
        useEconomyWebSocket(character);
        usePresenceSync();

        // Modal state
        const {
            activeModal, setActiveModal,
            locationCounts,
            doNotReceive, setDoNotReceive,
            handleMenuItemClick,
            handleOpenFriends,
            handleOpenMagic,
        } = useModalState(navigate);

        // Mail notifications
        const { handleMailIconClick } = useMailNotifications(character, setActiveModal);

        // Character skills
        const {
            abilitySkills, weaponSkills,
            isShowUpSkills,
            handleUpSkillsButtonClick,
            handleSaveUpSkills,
        } = useCharacterSkills(setActiveModal);

        // Page readiness
        const { showContent } = useAtomicPageReady(character, character?.location_slug);

        // Redux state
        const isRefreshing = useSelector(selectRefreshing);
        const hasUnreadMail = useSelector(selectHasUnreadMessages);
        const activeCharacterId = useSelector(state => state.local.activeCharacterId);

        // Derived values
        const CurrentPageComponent = character ? getComponentForLocation(character.location_slug)?.component : null;
        const locationConfig = character ? getComponentForLocation(character.location_slug) : null;
        const currentLocationConfig = locationConfig || { title: 'Вокзал', city: 'Авалон' };
        
        // 🔥 Ключевая проверка: мы внутри дома?
        const isInsideHouse = !!character?.current_house_id || character?.chat_room_id?.startsWith('house:');

        let computedTitle = '';
        
        if (isInsideHouse) {
            // Если мы в доме, мы ЖДЕМ точный chatRoomLabel. 
            // Пока он null/undefined, title остается пустой строкой. 
            // Никакого фоллбэка на location_slug ("Частные дома")!
            computedTitle = chatRoomLabel || '';
        } else {
            // Мы на улице, берем стандартный заголовок локации
            if (typeof currentLocationConfig?.title === "string") {
                computedTitle = currentLocationConfig.title;
            } else if (typeof currentLocationConfig?.title === "function" && character) {
                try { 
                    computedTitle = currentLocationConfig.title(character) || ''; 
                } catch (e) { 
                    console.error('Title compute error:', e); 
                    computedTitle = ''; 
                }
            }
        }

        // Low height detection
        useEffect(() => {
            const checkHeight = () => {
                if (window.innerHeight < 660) {
                    document.body.classList.add("low-height");
                } else {
                    document.body.classList.remove("low-height");
                }
            };

            checkHeight();
            window.addEventListener('resize', checkHeight);
            return () => window.removeEventListener('resize', checkHeight);
        }, []);

       

        // Clear caches on character change (SPA logout)
        useEffect(() => {                     
            dispatch(resetNavigation());
        }, [activeCharacterId, dispatch]);

        // Update document title
        useEffect(() => {
            if (character?.name) {
                document.title = `${character.name} - Эхо Смуты`;
            }
            return () => {
                document.title = 'Эхо Смуты';
            };
        }, [character?.name]);

        // Handlers
        const handleTradeButtonClick = (buttonId) => {
            dispatch(requestTradeAction({ id: buttonId, locationSlug: character?.location_slug }));
        };

        const { handleRefresh } = useBaseRefresh();
        const { handleLocationChange } = useLocationTransition(character, setActiveModal, showError);

        // Error state
        if (error) {
            return (
                <div className={styles.page}>
                    <div className={styles.errorContainer}>{error}</div>
                </div>
            );
        }

        // Loading state
        if (!character || !CurrentPageComponent) {
            return (
                <div className={styles.page}>
                    <main className={styles.mainContent}></main>
                </div>
            );
        }       
      

        return (
            <ErrorProvider>
                <ChatWebSocketProvider character={character}>
                    <div className={styles.page} style={{ '--panel-height': `${panelHeight}vh` }}>
                        {!showContent && (
                            <div style={{ 
                                position: 'fixed', 
                                top: 0, 
                                left: 0, 
                                right: 0, 
                                bottom: 0, 
                                backgroundColor: 'white', 
                                zIndex: 9999 
                            }}></div>
                        )}
                        <div style={{ opacity: showContent ? 1 : 0, pointerEvents: showContent ? 'auto' : 'none' }}>
                            <main className={styles.mainContent} style={{ height: `calc(100vh - ${panelHeight}vh)` }}>
                                <ErrorToast message={currentError} />
                                <TopBar
                                    title={computedTitle}
                                    city={currentLocationConfig.city}
                                    character={character}
                                    onMenuItemClick={handleMenuItemClick}
                                    onRefresh={handleRefresh}
                                    isRefreshing={isRefreshing}
                                    hasUnreadMail={hasUnreadMail}
                                    onMailClick={handleMailIconClick}
                                    onTradeButtonClick={handleTradeButtonClick}
                                />
                                <div className={styles.newPanel}>
                                    <div className={styles.content}>
                                        <CurrentPageComponent
                                            key={character?.id}
                                            character={character}
                                            onRefresh={handleRefresh}
                                            handleLocationChange={handleLocationChange}
                                            {...pageProps}
                                        />
                                    </div>
                                    <div className={styles.characterPanelNew}>
                                        <CharacterPanel
                                            character={character}
                                            onMenuItemClick={handleMenuItemClick}
                                            handleUpSkillsButtonClick={handleUpSkillsButtonClick}
                                            isShowUpSkills={isShowUpSkills}
                                        />
                                    </div>
                                </div>
                            </main>
                            <footer className={styles.footer}>
                                <BottomPanel
                                    character_id={character?.id}
                                    character_name={character?.name}
                                    roomId={isInsideHouse && !chatRoomLabel ? '' : (character?.chat_room_id ?? character?.location_slug)}
                                    roomLabel={chatRoomLabel}
                                    panelHeight={panelHeight}
                                    setPanelHeight={setPanelHeight}
                                />
                            </footer>
                            <Modals
                                activeModal={activeModal}
                                abilitySkills={abilitySkills}
                                weaponSkills={weaponSkills}            
                                doNotReceive={doNotReceive}
                                setDoNotReceive={setDoNotReceive}
                                character={character}
                                setActiveModal={setActiveModal}
                                handleOpenFriends={handleOpenFriends}
                                handleOpenMagic={handleOpenMagic}
                                handleSaveUpSkills={handleSaveUpSkills}
                                locationCounts={locationCounts}
                                handleLocationChange={handleLocationChange}
                                panelHeight={panelHeight}
                            />
                        </div>
                    </div>
                </ChatWebSocketProvider>
            </ErrorProvider>
        );
    };
}
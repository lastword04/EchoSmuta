import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';

import { ChatPanel } from './ChatPanel/ChatPanel';
import { UserListPanel } from './UserListPanel/UserListPanel';

import styles from './BottomPanel.module.css';

/**
 * Нижняя панель с чатом и списком онлайн.
 * Поддерживает ресайз высоты через перетаскивание верхней границы.
 */
const MAX_HEIGHT_VH = 100;

export const BottomPanel = ({ 
    character_id, 
    character_name, 
    character_level, 
    roomId, 
    roomLabel,
    panelHeight, 
    setPanelHeight 
}) => {
    const activeTab = useSelector((state) => state.session.activeTab);
    const activeChatRoom = activeTab === 'Локация' ? roomId : 'global';
    const [isResizing, setIsResizing] = useState(false);
    
    // Refs для значений, чтобы они были актуальны внутри слушателей событий
    const startYRef = useRef(0);
    const startHeightRef = useRef(0);
    const windowHeight = useRef(window.innerHeight);
    const resizeHandleRef = useRef(null);

    // Обновляем высоту окна при ресайзе браузера
    useEffect(() => {
        const update = () => (windowHeight.current = window.innerHeight);
        window.addEventListener('resize', update);
        return () => window.removeEventListener('resize', update);
    }, []);

    // Логика начала ресайза
    const startResize = useCallback((e) => {
        if (e.cancelable) e.preventDefault();
        document.body.style.userSelect = 'none';
        setIsResizing(true);
        startYRef.current = e.touches ? e.touches[0].clientY : e.clientY;
        startHeightRef.current = panelHeight;
    }, [panelHeight]);

    // Логика процесса ресайза
    useEffect(() => {
        if (!isResizing) return;

        // Вычисляем минимальную высоту здесь (зависит от windowHeight.current)
        const minHeightVh = 8 / (windowHeight.current / 100);

        const onResize = (e) => {
            // Блокируем нативный скролл при движении пальцем
            if (e.cancelable && e.type === 'touchmove') {
                e.preventDefault();
            }

            const currentY = e.touches ? e.touches[0].clientY : e.clientY;
            const deltaPx = startYRef.current - currentY;
            const deltaVh = (deltaPx / windowHeight.current) * 100;
            const newHeightVh = Math.min(Math.max(startHeightRef.current + deltaVh, minHeightVh), MAX_HEIGHT_VH);
            
            setPanelHeight(newHeightVh);
        };

        const stopResize = () => {
            document.body.style.userSelect = '';
            setIsResizing(false);
        };

        window.addEventListener('mousemove', onResize);
        window.addEventListener('mouseup', stopResize);
        // passive: false для touchmove, чтобы работал preventDefault
        window.addEventListener('touchmove', onResize, { passive: false });
        window.addEventListener('touchend', stopResize);

        return () => {
            window.removeEventListener('mousemove', onResize);
            window.removeEventListener('mouseup', stopResize);
            window.removeEventListener('touchmove', onResize);
            window.removeEventListener('touchend', stopResize);
        };
    }, [isResizing, setPanelHeight]);

    // Привязка событий к ручке ресайза (решает проблему "Unable to preventDefault inside passive event listener")
    useEffect(() => {
        const node = resizeHandleRef.current;
        if (!node) return;

        const onStart = (e) => startResize(e);

        node.addEventListener('touchstart', onStart, { passive: false });
        node.addEventListener('mousedown', onStart);

        return () => {
            node.removeEventListener('touchstart', onStart);
            node.removeEventListener('mousedown', onStart);
        };
    }, [startResize]);

    return (
        <div className={styles.bottomPanel}>
            <div
                className={styles.bottomPanelFixed}
                style={{
                    height: `${panelHeight}vh`,
                }}
            >
                <div 
                    className={styles.topBorder} 
                    ref={resizeHandleRef} 
                    style={{ touchAction: 'none' }}
                />
                
                <div className={styles.panelsRow}>
                    <div className={styles.chatWrap}>
                        <ChatPanel activeChatRoom={activeChatRoom} roomId={roomId}/>
                    </div>
                    <div className={styles.verticalBorder} />
                    <div className={styles.usersWrap}>
                        <UserListPanel
                            character_id={character_id}
                            character_name={character_name}
                            character_level={character_level}
                            roomId={roomId}
                            roomLabel={roomLabel}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};
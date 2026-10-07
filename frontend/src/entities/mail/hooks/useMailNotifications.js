import { useEffect, useCallback } from 'react';
import { useDispatch } from 'react-redux';

import { mailApi, useGetInboxQuery, useGetSentQuery } from '../api/mailApi';
import { checkUnreadMail } from '../store/mailSlice';

/**
 * Домен почты: слушает window event 'mail-notification' от единого сокета
 * (ChatWebSocketProvider) и обновляет RTK Query кэш писем.
 * 
 * Сокет больше не создаётся — это делает useGlobalWebSocket в withBasePage.
 */
export const useMailNotifications = (character, setActiveModal) => {
    const dispatch = useDispatch();
    
    // Стр.1 обеих вкладок ВСЕГДА в кэше:
    // — модалка открывается в первом же кадре
    // — new_mail через WebSocket обновляет список даже с закрытой модалкой
    const isReady = Boolean(character?.id);
    useGetInboxQuery({ limit: 10, offset: 0 }, { skip: !isReady });
    useGetSentQuery({ limit: 10, offset: 0 }, { skip: !isReady });

    const handleMailNotification = useCallback((event) => {
        if (event.detail?.event_type === 'new_mail') {
            dispatch(checkUnreadMail());
            dispatch(mailApi.util.invalidateTags(['Mail']));
        }
    }, [dispatch]);

    const handleMailIconClick = () => {    
        setActiveModal('MAIL_MODAL');
    };

    useEffect(() => {
        if (!character?.id) return;    
        dispatch(checkUnreadMail());

        window.addEventListener('mail-notification', handleMailNotification);
        return () => {      
            window.removeEventListener('mail-notification', handleMailNotification);
        };
    }, [character?.id, dispatch, handleMailNotification]);

    return {
        handleMailIconClick,
    };
};
import { useContext } from 'react';
import { ChatWebSocketContext } from '../../../shared/lib/context/ChatWebSocketContext';

/**
 * Хук для отправки сообщений в чат.
 * Используется в ChatPanel вместо старого useChatWebSocket.
 *
 * Автоматически добавляет `room` в payload на основе активной вкладки чата
 * (это делает ChatWebSocketProvider). Сам хук только читает контекст.
 *
 * Перенесён из shared/hooks/websocket/useGlobalWebSocket.jsx в рамках
 * FSD-рефакторинга: потребитель хука — виджет ChatPanel, а слой entities
 * имеет право импортировать из shared (контекст).
 */
export const useChatSend = () => {
    return useContext(ChatWebSocketContext) || (() => false);
};

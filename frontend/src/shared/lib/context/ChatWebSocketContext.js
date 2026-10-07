import { createContext } from 'react';

/**
 * Контракт единого WebSocket-сокета чата (см. ChatWebSocketProvider в
 * app/providers/hooks/useGlobalWebSocket.jsx): значение в провайдере —
 * функция send(payload), автоматически добавляющая room в payload.
 *
 * Живёт в shared, чтобы контракт был доступен и провайдеру (app → shared),
 * и хуку useChatSend (entities/chat/hooks → shared), не создавая
 * запрещённого ребра entities → app. Выделен из useGlobalWebSocket.jsx
 * (бывш. shared/hooks/websocket) в рамках FSD-рефакторинга.
 */
export const ChatWebSocketContext = createContext(null);

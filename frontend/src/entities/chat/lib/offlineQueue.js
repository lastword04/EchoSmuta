// shared/lib/offlineQueue.js

const queue = [];

export const addToOfflineQueue = (message) => {
  queue.push({
    ...message,
    queuedAt: Date.now(),
  });
  return queue.length;
};

export const flushOfflineQueue = () => {
  const messages = [...queue];
  queue.length = 0;
  return messages;
};

export const getQueueSize = () => queue.length;
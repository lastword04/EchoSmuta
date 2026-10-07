import { useState, useEffect } from 'react';

/**
 * Изолированный компонент часов. Обновляется каждую секунду,
 * но не триггерит ре-рендер всего TopBar.
 */
export const ServerClock = () => {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  
  const formattedTime = time.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  
  return <span className="time">{formattedTime}</span>;
};
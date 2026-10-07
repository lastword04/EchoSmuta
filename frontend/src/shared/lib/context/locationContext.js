import { createContext, useContext } from 'react';

/**
 * Контекст для доступа к реестру локаций.
 * Предоставляет функцию getComponentForLocation.
 */
export const LocationContext = createContext(null);

/**
 * Хук для получения функции getComponentForLocation из контекста.
 */
export const useLocationRegistry = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocationRegistry must be used within LocationContext.Provider');
  }
  return context;
};

import React, { useEffect } from 'react';
import { Provider, useDispatch } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './providers/store';
import { ThemeInitializer } from './providers/ThemeInitializer';
import { AppRouter } from './providers/router';
import { clearActiveCharacterId } from '../shared/store/activeCharacterIdSlice';
import { clearActiveCharacterName } from '../shared/store/activeCharacterNameSlice';
import { setupGlobalScrollHiding } from '../shared/lib/utils/scrollHiding';
import './styles/globals.css';

// === Компонент для обработки бана (должен быть внутри Provider) ===
const BanHandler = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    const handleUserBanned = (event) => {
      const message = event.detail?.message || 'Вы забанены администратором';

      // Показываем alert
      alert(`⚠️ ${message}\n\nВы будете перенаправлены на главную страницу.`);

      // Очищаем Redux состояние персонажа
      dispatch(clearActiveCharacterId());
      dispatch(clearActiveCharacterName());

      // Очищаем localStorage и sessionStorage (persist данные)
      localStorage.clear();
      sessionStorage.clear();

      // Перенаправляем на главную
      window.location.href = '/';
    };

    window.addEventListener('user-banned', handleUserBanned);

    return () => {
      window.removeEventListener('user-banned', handleUserBanned);
    };
  }, [dispatch]);

  return null; // Не рендерит ничего
};

export const App = () => {
  // === Управление видимостью скроллов ===
  // === Управление видимостью скроллов — реализация в shared/lib/scrollHiding.js ===
  useEffect(() => setupGlobalScrollHiding(), []);

  return (
    <Provider store={store}>
      <PersistGate persistor={persistor}>
        <BanHandler />
        <ThemeInitializer />
        <BrowserRouter>
          <AppRouter />
        </BrowserRouter>
      </PersistGate>
    </Provider>
  );
};
import { useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { clearActiveCharacterId } from '../../../shared/store/activeCharacterIdSlice';
import { clearActiveCharacterName } from '../../../shared/store/activeCharacterNameSlice';
import { clearUserRole } from '../../../shared/store/userRoleSlice';


// Страницы уровня «аккаунт»: доступны без активного персонажа.
// Авторизация на них проверяется цепочкой 401 → notifyAuthError → auth-error.
const ACCOUNT_ROUTES = ['/characters', '/admin'];

export const ProtectedRoute = ({ children }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  // ВАЖНО: persistReducer'ы обёрнуты на ВЕТКАХ стора (rootReducer.js:
  // `local` и `session`), поэтому флаг rehydration живёт внутри ветки,
  // а не в корневом state._persist.
  const rehydrated = useSelector((state) =>
    Boolean(state.local?._persist?.rehydrated)
  );
  const activeCharacterId = useSelector(
    (state) => state.local?.activeCharacterId
  );

  useEffect(() => {
    const handleAuthError = () => {
      dispatch(clearActiveCharacterId());
      dispatch(clearActiveCharacterName());
      dispatch(clearUserRole());

      navigate('/login', {
        replace: true,
        state: {
          authRequired: 'Для доступа к этой странице требуется авторизация.',
          from: location.pathname,
        },
      });
    };

    const handleCharacterNotOnline = (event) => {
      console.log('Character is not online:', event.detail);
      navigate('/characters');
    };

    window.addEventListener('auth-error', handleAuthError);
    window.addEventListener('character-not-online', handleCharacterNotOnline);

    return () => {
      window.removeEventListener('auth-error', handleAuthError);
      window.removeEventListener('character-not-online', handleCharacterNotOnline);
    };
  }, [dispatch, navigate, location.pathname]);
  

  if (!rehydrated) {
    return null;
  }

  const isAccountRoute = ACCOUNT_ROUTES.some(
    (route) => location.pathname === route || location.pathname.startsWith(route + '/')
  );

  // Игровые маршруты требуют активного персонажа.
  // Если его нет — на выбор персонажа, а НЕ на логин.
  if (!isAccountRoute && !activeCharacterId) {
    return <Navigate to="/characters" replace />;
  }

  return children;
};

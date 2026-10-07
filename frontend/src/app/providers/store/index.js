import { configureStore } from '@reduxjs/toolkit';
import { persistStore } from 'redux-persist';
import rootReducer from './rootReducer';
import { storeRef } from '../../../shared/store/storeRef';
import { clearActiveCharacterId } from '../../../shared/store/activeCharacterIdSlice';
import { clearActiveCharacterName } from '../../../shared/store/activeCharacterNameSlice';
import { clearUserRole } from '../../../shared/store/userRoleSlice';
import { captchaApi } from '../../../entities/captcha/api/captchaApi';
import { captchaMutationApi } from '../../../entities/captcha/api/captchaApi';
import { characterStatsApi } from '../../../entities/character/api/characterStatsApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { tavernApi } from '../../../entities/economy/api/tavernApi';
import { restApi } from '../../../entities/character/api/restApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { resourcesApi } from '../../../entities/resources/api/resourcesApi';
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { mailApi } from '../../../entities/mail/api/mailApi';
import { categoryApi } from '../../../entities/mail/api/categoryApi';
import { chatApi } from '../../../entities/chat/api/chatApi';
import { panelApi } from '../../../entities/character/api/panelApi';
import { notebookApi } from '../../../entities/character/api/notebookApi';
import { currencyApi } from '../../../entities/character/api/currencyApi';
import { authGameApi } from '../../../entities/auth/api/authGameApi';
import { authLogoutApi } from '../../../entities/auth/api/authLogoutApi';
import { authTokenApi } from '../../../entities/auth/api/authTokenApi';
import { authApi } from '../../../entities/auth/api/authApi';
import { forumApi } from '../../../entities/forum/api/forumApi';
import { commentApi } from '../../../entities/forum/api/commentApi';
import { fileApi } from '../../../entities/file/api/fileApi';

import { characterAdminApi } from '../../../entities/admin/api/character/charactersAdminApi';
import { economyAdminApi } from '../../../entities/admin/api/economy/economyAdminApi';
import { miningAdminApi } from '../../../entities/admin/api/mining/miningAdminApi';
import { usersAdminApi } from '../../../entities/admin/api/users/usersAdminApi';
import { authAdminApi } from '../../../entities/admin/api/auth/authAdminApi';


// Создаем хранилище с поддержкой redux-persist
export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE', 'persist/PURGE'],
      },
    }).concat(      
      captchaApi.middleware,
      captchaMutationApi.middleware,
      characterStatsApi.middleware,
      characterApi.middleware,      
      currencyApi.middleware,
      economyApi.middleware,
      tavernApi.middleware,
      restApi.middleware,    
      housesApi.middleware,  
      inventoryApi.middleware,      
      resourcesApi.middleware,      
      mailApi.middleware,
      categoryApi.middleware,
      chatApi.middleware,      
      panelApi.middleware,
      notebookApi.middleware,     
      authGameApi.middleware,
      authLogoutApi.middleware,
      authTokenApi.middleware,
      authApi.middleware,
      forumApi.middleware,
      commentApi.middleware,
      fileApi.middleware,

      characterAdminApi.middleware,
      economyAdminApi.middleware,
      miningAdminApi.middleware,
      usersAdminApi.middleware,
      authAdminApi.middleware,
    ),
  devTools: import.meta.env.DEV,
});

// Возвращаем persistor и хранилище
export const persistor = persistStore(store);

// Единая точка очистки persist-признаков входа при истёкшей авторизации.
// Событие 'auth-error' диспатчат notifyAuthError() из shared/api/baseQuery.js
// (RTK Query) и axios-интерцептор (axiosInstance.js) при провале refresh.
// Раньше очистка выполнялась прямо в baseQuery.js через store.dispatch,
// но импорт store там создавал циклический импорт
// baseQuery → store/index → rootReducer → api-слайсы → baseQuery
// и TDZ-падение «Cannot access 'createAxiosBaseQuery' before initialization»
// в первом api-слайсе графа (characterApi.js:7).
window.addEventListener('auth-error', () => {
  store.dispatch(clearActiveCharacterId());
  store.dispatch(clearActiveCharacterName());
  store.dispatch(clearUserRole());
});

// Регистрируем синглтон для императивного доступа из нижних слоёв (см. storeRef.js)
storeRef.current = store;

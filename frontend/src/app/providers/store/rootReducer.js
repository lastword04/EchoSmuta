import { combineReducers } from '@reduxjs/toolkit';
import { persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import storageSession from 'redux-persist/lib/storage/session';
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { captchaApi } from '../../../entities/captcha/api/captchaApi';
import { captchaMutationApi } from '../../../entities/captcha/api/captchaApi';
import { characterStatsApi } from '../../../entities/character/api/characterStatsApi';
import { characterApi } from '../../../entities/character/api/characterApi';
import { economyApi } from '../../../entities/economy/api/economyApi';
import { tavernApi } from '../../../entities/economy/api/tavernApi';
import { restApi } from '../../../entities/character/api/restApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { resourcesApi } from '../../../entities/resources/api/resourcesApi';
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

import { economyAdminApi } from '../../../entities/admin/api/economy/economyAdminApi';
import { miningAdminApi } from '../../../entities/admin/api/mining/miningAdminApi';
import { characterAdminApi } from '../../../entities/admin/api/character/charactersAdminApi';
import { usersAdminApi } from '../../../entities/admin/api/users/usersAdminApi';
import { authAdminApi } from '../../../entities/admin/api/auth/authAdminApi';

import mailReducer from '../../../entities/mail/store/mailSlice'
import visitReducer from '../../../entities/auth/store/visitSlice';
import refreshReducer from './refreshSlice'
import activeTabReducer from '../../../shared/store/activeTabSlice';
import modeReducer from '../../../shared/store/modeSlice';
import activeCharacterNameReducer from '../../../shared/store/activeCharacterNameSlice';
import activeCharacterIdReducer from '../../../shared/store/activeCharacterIdSlice';
import userRoleReducer from '../../../shared/store/userRoleSlice';
import pendingCreateTopicReducer from '../../../entities/forum/store/pendingCreateTopicSlice';
import pendingCommentReducer from '../../../entities/forum/store/pendingCommentSlice';
import miningReducer from '../../../entities/resources/store/miningSlice';
import craftingReducer from '../../../features/city-trade/store/craftingSlice';
import locationNavigationReducer from '../../../shared/store/locationNavigationSlice';
import topBarActionsReducer from '../../../shared/store/topBarActionsSlice';
import characterReducer from '../../../entities/character/store/characterSlice';
import houseUiReducer from '../../../entities/character/store/houseUiSlice';



const localStorageConfig = {
  key: 'local',
  storage: storage,
};

const sessionStorageConfig = {
  key: 'session',
  storage: storageSession,
};

const rootReducer = combineReducers({
  [inventoryApi.reducerPath]: inventoryApi.reducer,
  [captchaApi.reducerPath]: captchaApi.reducer,
  [captchaMutationApi.reducerPath]: captchaMutationApi.reducer,
  [characterStatsApi.reducerPath]: characterStatsApi.reducer,
  [characterApi.reducerPath]: characterApi.reducer,
  [economyApi.reducerPath]: economyApi.reducer,
  [tavernApi.reducerPath]: tavernApi.reducer,
  [restApi.reducerPath]: restApi.reducer,
  [housesApi.reducerPath]: housesApi.reducer,
  [resourcesApi.reducerPath]: resourcesApi.reducer,
  [mailApi.reducerPath]: mailApi.reducer,
  [categoryApi.reducerPath]: categoryApi.reducer,
  [chatApi.reducerPath]: chatApi.reducer,
  [panelApi.reducerPath]: panelApi.reducer,
  [notebookApi.reducerPath]: notebookApi.reducer,
  [currencyApi.reducerPath]: currencyApi.reducer,
  [authGameApi.reducerPath]: authGameApi.reducer,
  [authLogoutApi.reducerPath]: authLogoutApi.reducer,
  [authTokenApi.reducerPath]: authTokenApi.reducer,
  [authApi.reducerPath]: authApi.reducer,
  [forumApi.reducerPath]: forumApi.reducer,
  [commentApi.reducerPath]: commentApi.reducer,
  [fileApi.reducerPath]: fileApi.reducer,
  
  [economyAdminApi.reducerPath]: economyAdminApi.reducer,
  [miningAdminApi.reducerPath]: miningAdminApi.reducer,  
  [characterAdminApi.reducerPath]: characterAdminApi.reducer,
  [usersAdminApi.reducerPath]: usersAdminApi.reducer,
  [authAdminApi.reducerPath]: authAdminApi.reducer,

  locationNavigation: locationNavigationReducer, 
  topBarActions: topBarActionsReducer, 
  character: characterReducer,
  mail: mailReducer,
  visit: visitReducer,
  refresh: refreshReducer,  
  houseUi: houseUiReducer,
  
  
  local: persistReducer(localStorageConfig, combineReducers({
    mode: modeReducer,
    activeCharacterName: activeCharacterNameReducer,
    activeCharacterId: activeCharacterIdReducer,   
    userRole: userRoleReducer,       
  })),
  
  session: persistReducer(sessionStorageConfig, combineReducers({
    activeTab: activeTabReducer,
    pendingCreateTopic: pendingCreateTopicReducer,
    pendingComment: pendingCommentReducer,
    mining: miningReducer,
    crafting: craftingReducer,            
  })),
});

export default rootReducer;

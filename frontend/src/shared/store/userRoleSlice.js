import { createSlice } from '@reduxjs/toolkit';

// Роль пользователя — строковое значение UserRole с бэкенда:
// 'user' | 'moderator' | 'admin' (см. services/*/shared/enums.py).
// Заполняется из ответа логина (dataLogin.user.role) и хранится
// в persist-ветке `local`. Нужна AdminPage для синхронного гарда
// /admin без сетевой пробы и без спиннера.
const userRoleSlice = createSlice({
  name: 'userRole',
  initialState: null,
  reducers: {
    setUserRole: (state, action) => {
      return action.payload;
    },
    clearUserRole: () => null,
  },
});

export default userRoleSlice.reducer;
export const { setUserRole, clearUserRole } = userRoleSlice.actions;
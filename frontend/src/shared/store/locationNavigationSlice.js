import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  pendingLocationSlug: null,   // цель текущего перехода (null = нет перехода)
  activeView: null,            // активная вкладка (унифицированная для текущей локации)
  phase: 'idle',               // idle | changing-location | ready | error
  requestId: 0,                // монотонный счётчик для защиты от устаревших ответов
};

const locationNavigationSlice = createSlice({
  name: 'locationNavigation',
  initialState,
  reducers: {
    startLocationChange: (state, action) => {
      const { targetSlug, requestId } = action.payload;
      state.pendingLocationSlug = targetSlug;
      state.phase = 'changing-location';
      state.requestId = requestId;
      // activeView НЕ трогаем: он меняется только вместе с character,
      // иначе контент текущей локации мелькает в момент клика
    },
    confirmLocation: (state, action) => {
      if (state.requestId !== action.payload.requestId) return; // устаревший ответ
      state.pendingLocationSlug = null;
      state.phase = 'ready';
    },
    failLocationChange: (state, action) => {
      if (state.requestId !== action.payload.requestId) return;
      state.pendingLocationSlug = null;
      state.phase = 'idle'; // не error, чтобы не блокировать UI
    },
    selectView: (state, action) => {
      state.activeView = action.payload.viewId;
    },
    resetNavigation: () => initialState,
  },
});

export const {
  startLocationChange,
  confirmLocation,
  failLocationChange,
  selectView,
  resetNavigation,
} = locationNavigationSlice.actions;

export default locationNavigationSlice.reducer;
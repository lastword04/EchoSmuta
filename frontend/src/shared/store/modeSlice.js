import { createSlice } from '@reduxjs/toolkit';

const DEFAULT_MODE = 'day'; // 'day' | 'night'

const modeSlice = createSlice({
  name: 'mode',
  initialState: DEFAULT_MODE,
  reducers: {
    // Просто возвращаем новое значение
    setMode: (state, action) => {
      return action.payload;
    },
    
    // Просто переключаем значение
    toggleMode: (state) => {
      return state === 'day' ? 'night' : 'day';
    },
    
    // Сброс к дефолту
    resetMode: () => DEFAULT_MODE,
  },
});

export default modeSlice.reducer;
export const { setMode, toggleMode, resetMode } = modeSlice.actions;
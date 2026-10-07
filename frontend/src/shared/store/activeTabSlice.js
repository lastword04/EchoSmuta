import { createSlice } from '@reduxjs/toolkit';

// Первичное состояние (инициализируем с сохранённого значения из sessionStorage)
const DEFAULT_TAB = 'Общий';

// Создаём слайс
const activeTabSlice = createSlice({
  name: 'activeTab',
  initialState: DEFAULT_TAB,
  reducers: {
    setActiveTab: (state, action) => {
      return action.payload;
    },
    removeActiveTab: () => DEFAULT_TAB,
  },
});

// Экспорт редукера и экшонов
export default activeTabSlice.reducer;
export const { setActiveTab, removeActiveTab } = activeTabSlice.actions;
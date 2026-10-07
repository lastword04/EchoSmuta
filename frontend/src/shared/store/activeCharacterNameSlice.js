import { createSlice } from '@reduxjs/toolkit';

const activeCharacterNameSlice = createSlice({
  name: 'activeCharacterName',
  initialState: null,
  reducers: {
    setActiveCharacterName: (state, action) => {
      return action.payload;
    },
    clearActiveCharacterName: () => null,
  },
});

export default activeCharacterNameSlice.reducer;
export const { setActiveCharacterName, clearActiveCharacterName } = activeCharacterNameSlice.actions;
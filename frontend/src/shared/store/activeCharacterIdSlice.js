import { createSlice } from '@reduxjs/toolkit';

const activeCharacterIdSlice = createSlice({
  name: 'activeCharacterId',
  initialState: null,
  reducers: {
    setActiveCharacterId: (state, action) => {
      return action.payload;
    },
    clearActiveCharacterId: () => null,
  },
});

export default activeCharacterIdSlice.reducer;
export const { setActiveCharacterId, clearActiveCharacterId } = activeCharacterIdSlice.actions;
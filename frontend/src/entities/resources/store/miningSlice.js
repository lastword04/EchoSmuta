import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  lastMiningId: null,
  locationSlug: null
};

const miningSlice = createSlice({
  name: 'mining',
  initialState,
  reducers: {
    setLastMining: (state, action) => {
        state.lastMiningId = action.payload?.lastMiningId ?? null;
        state.locationSlug = action.payload?.locationSlug ?? null;
    }, 
    clearLastMining: (state) => {
      state.lastMiningId = null;
      state.locationSlug = null;
    }, 
  },
});

export const { setLastMining, clearLastMining } = miningSlice.actions;
export default miningSlice.reducer;
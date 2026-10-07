import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  lastAction: null, // { type, payload, timestamp, consumed }
};

const topBarActionsSlice = createSlice({
  name: 'topBarActions',
  initialState,
  reducers: {
    requestTradeAction: (state, action) => {
      const { id, locationSlug } = action.payload;
      state.lastAction = {
        type: 'TRADE_BUTTON_CLICK',
        payload: { id, locationSlug },
        timestamp: Date.now(),
        consumed: false,
      };
    },
    consumeAction: (state) => {
      if (state.lastAction) {
        state.lastAction.consumed = true;
      }
    },
    clearAction: (state) => {
      state.lastAction = null;
    },
  },
});

export const {
  requestTradeAction,
  consumeAction,
  clearAction,
} = topBarActionsSlice.actions;

export default topBarActionsSlice.reducer;
// src/store/slices/visitSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  visitId: null,
  visitData: null,
  isLoading: false,
  error: null,
  isInitialized: false, // флаг что запрос уже был сделан
};

const visitSlice = createSlice({
  name: 'visit',
  initialState,
  reducers: {
    setVisitLoading: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    setVisitSuccess: (state, action) => {
      state.visitId = action.payload.id;
      state.visitData = action.payload;
      state.isLoading = false;
      state.isInitialized = true;
      state.error = null;
    },
    setVisitError: (state, action) => {
      state.isLoading = false;
      state.error = action.payload;
      state.isInitialized = true;
    },
    clearVisit: (state) => {
      state.visitId = null;
      state.visitData = null;
      state.error = null;
      state.isInitialized = false;
    },
  },
});

export const { setVisitLoading, setVisitSuccess, setVisitError, clearVisit } = visitSlice.actions;
export default visitSlice.reducer;

// Селекторы
export const selectVisitId = (state) => state.visit.visitId;
export const selectVisitData = (state) => state.visit.visitData;
export const selectIsVisitLoading = (state) => state.visit.isLoading;
export const selectIsVisitInitialized = (state) => state.visit.isInitialized;
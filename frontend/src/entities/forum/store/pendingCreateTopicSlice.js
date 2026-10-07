import { createSlice } from '@reduxjs/toolkit';

const pendingCreateTopicSlice = createSlice({
  name: 'pendingCreateTopic',
  initialState: null, // { forumId: string, forumName: string } | null
  reducers: {
    setPendingCreateTopic: (state, action) => {
      return action.payload; // { forumId, forumName }
    },
    clearPendingCreateTopic: () => null,
  },
});

export default pendingCreateTopicSlice.reducer;
export const { setPendingCreateTopic, clearPendingCreateTopic } = pendingCreateTopicSlice.actions;
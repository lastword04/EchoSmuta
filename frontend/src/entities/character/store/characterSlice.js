// frontend/src/entities/character/store/characterSlice.js
import { createSlice, createSelector } from '@reduxjs/toolkit';

import {
  clearActiveCharacterId,
  setActiveCharacterId,
} from '../../../shared/store/activeCharacterIdSlice';

/**
 * Вариант C: состояние — четыре независимые корзины.
 *
 *  - snapshot     — сырой REST-снапшот (getOnlyMe). Заменяется целиком,
 *                   без правил слияния на записи.
 *  - volatile     — поля, которыми владеет WebSocket (и REST /buffs для buffs).
 *                   Пишутся по мере прихода, частичный payload допустим.
 *  - locationSlug — владеет ТОЛЬКО коммит перехода (commitLocation/setLocation).
 *  - chatRoomId   — виртуальное пространство для чата. Владеет коммит перехода
 *                   (commitLocation сбрасывает на locationSlug, commitChatRoom
 *                   устанавливает 'house:uuid' / 'inn:inside').
 *
 * Объект персонажа собирается НА ЧТЕНИИ (selectCharacter): volatile перекрывает
 * snapshot, location_slug берётся из locationSlug, chat_room_id — из chatRoomId.
 * Поэтому снапшот физически не может затереть ни одно из них.
 *
 * Состояние НЕ персистится: volatile не должны переживать перезагрузку.
 */

export const VOLATILE_FIELDS = [
  'health',
  'mana',
  'tiredness',
  'equipment_bonuses',
  'buffs',
  'effective_power',
  'effective_agility',
  'effective_lucky',
  'effective_max_health',
  'effective_max_mana',
  'effective_max_tiredness',
];

const initialState = { snapshot: null, volatile: {}, locationSlug: null, chatRoomId: null };

const characterSlice = createSlice({
  name: 'character',
  initialState,
  reducers: {
    /**
     * REST-снапшот. Пишется СЫРОМ в свою корзину — без merge-правил.
     * REST-баффы (если приехали) пишутся в volatile.buffs: для баффов
     * REST и WS равноправные источники, last-writer-wins.
     * Первый снапшот ждёт баффы, чтобы не мигать пустым списком.
     */
    applySnapshot: (state, action) => {
      const { character, buffs, buffsIsFetching = false } = action.payload || {};
      if (!character) return initialState;

      const isFirst = !state.snapshot || state.snapshot.id !== character.id;
      if (isFirst && buffsIsFetching) return; // ждём баффы

      if (isFirst) {
        state.snapshot = character;
        state.volatile = buffs !== undefined ? { buffs } : {};
        state.locationSlug = null;
        // chatRoomId инициализируется значением из бэка.
        // Для большинства локаций это null → чат использует location_slug.
        // Для тех, кто внутри дома/номера при F5, сразу приходит 'house:uuid' / 'inn:inside'.
        state.chatRoomId = character.current_room_id ?? null;
        return;
      }

      state.snapshot = character;
      if (buffs !== undefined) state.volatile.buffs = buffs;
    },

    /**
     * WS-тики. Пишем только известные volatile-поля, пропускаем null/undefined
     * (частичный payload publish_regeneration) и служебные ключи (event).
     */
    applyVolatile: (state, action) => {
      if (!state.snapshot) return;
      const stats = action.payload || {};
      for (const key of VOLATILE_FIELDS) {
        const value = stats[key];
        if (value != null) state.volatile[key] = value;
      }
    },

    /** Только смена локации (без ответа мутации). */
    setLocation: (state, action) => {
      if (!state.snapshot) return;
      state.locationSlug = action.payload;
      state.chatRoomId = action.payload;
    },

    /**
     * Атомарный коммит перехода: location_slug + слияние ответа мутации
     * в snapshot. volatile не трогаем — на чтении он перекроет snapshot сам.
     */
    commitLocation: (state, action) => {
      if (!state.snapshot) return;
      const { locationSlug, character } = action.payload || {};
      state.locationSlug = locationSlug;
      if (character) state.snapshot = { ...state.snapshot, ...character };
      // chatRoomId: приоритет за свежим current_room_id из ответа мутации.
      // Бэк мог выполнить автовход в номер при возврате в гостиницу —
      // тогда current_room_id = 'inn:inside', и чат должен туда переключиться.
      // Если бэк вернул null (обычная локация / выход из дома) — используем locationSlug.
      state.chatRoomId = character?.current_room_id ?? locationSlug;
    },

    /**
     * Коммит смены виртуальной комнаты для чата. Владеет ТОЛЬКО логика
     * переходов внутри пространств (вход/выход из дома, аренда номера).
     * Не вызывается при смене локации через карту — там chatRoomId
     * сбрасывается автоматически внутри commitLocation/setLocation.
     */
    commitChatRoom: (state, action) => {
      if (!state.snapshot) return;
      state.chatRoomId = action.payload;
    },

    /**
     * Оптимистичное обновление отдельных полей персонажа.
     * Используется UI-фичами (аренда номера, вход в дом и т.п.), чтобы
     * не ждать REST-рефетч snapshot и не показывать промежуточный кадр.
     */
    commitCharacterFields: (state, action) => {
      if (!state.snapshot) return;
      state.snapshot = { ...state.snapshot, ...action.payload };
    },

    /**
     * Очистка volatile при reconnect WS (self-healing).
     * После этого REST-рефетч обновит snapshot (включая effective_*),
     * а следующие WS-тики заполнят volatile заново.
     */
    clearVolatile: (state) => {
      state.volatile = {};
    },

    clearCharacter: () => initialState,
  },

  extraReducers: (builder) => {
    builder
      // Логаут (auth-error) — чистим, чтобы SPA не показал чужого персонажа
      .addCase(clearActiveCharacterId, () => initialState)
      // Вход/смена персонажа — сбрасываем прошлый снапшот
      .addCase(setActiveCharacterId, (state, action) => {
        if (state.snapshot && state.snapshot.id === action.payload) return;
        return initialState;
      });
  },
});

export const {
  applySnapshot,
  applyVolatile,
  setLocation,
  commitLocation,
  commitCharacterFields,
  commitChatRoom,
  clearCharacter,
  clearVolatile,
} = characterSlice.actions;

// ── Селекторы ──

const selectCharacterState = (state) => state.character;

/** Собранный персонаж: snapshot + volatile поверх + location_slug из коммита. */
export const selectCharacter = createSelector(
  [selectCharacterState],
  ({ snapshot, volatile, locationSlug, chatRoomId }) => {
    if (!snapshot) return null;
    const assembled = { ...snapshot };
    for (const field of VOLATILE_FIELDS) {
      if (volatile[field] !== undefined) assembled[field] = volatile[field];
    }
    assembled.location_slug = locationSlug ?? snapshot.location_slug;
    // chat_room_id — виртуальное пространство для чата.
    // null → чат использует location_slug (обычная локация).
    // 'house:uuid' / 'inn:inside' → чат изолирован в этой комнате.
    assembled.chat_room_id = chatRoomId ?? null;
    return assembled;
  }
);

export const selectCharacterId = (state) => state.character?.snapshot?.id ?? null;
export const selectCharacterLocation = (state) =>
  state.character?.locationSlug ?? state.character?.snapshot?.location_slug ?? null;
export const selectCharacterChatRoomId = (state) =>
  state.character?.chatRoomId ?? null;
export const selectCharacterBuffs = createSelector(
  [selectCharacter],
  (character) => character?.buffs ?? []
);

export default characterSlice.reducer;
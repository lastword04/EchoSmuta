import { createApi } from '@reduxjs/toolkit/query/react';
import { characterApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const characterApi = createApi({
  reducerPath: 'characterApi',
  baseQuery: createAxiosBaseQuery(characterApiInstance),  
  tagTypes: ['Character', 'Skills', 'LocationStats', 'CharacterInfo', 'AppliedSkills', 
  'MyCharacters', 'CreationStatus', 'DetachedStatus', 'DetachedCharacters', 
  'TransferRules', 'ReferralLink', 'CharacterFull'],
  endpoints: (builder) => ({
    // ═══ QUERIES (чтение) ═══
    getOnlyMe: builder.query({
      query: () => ({ url: '/only-me', method: 'GET' }),
      providesTags: ['Character'],
      keepUnusedDataFor: 5 * 60,
    }),

    getCharacterSkills: builder.query({
      query: () => ({
        url: '/skills/',
        method: 'GET',
      }),
      providesTags: ['Skills'],
      keepUnusedDataFor: 300, // 5 минут — данные нужны для модалки и кнопки
    }),

    getLocationsStats: builder.query({
      query: () => ({
        url: '/locations/count',
        method: 'GET',
      }),
      providesTags: ['LocationStats'],
      keepUnusedDataFor: 300, // 5 минут — для карты
    }),

    // ═══ MUTATIONS (изменения) ═══    

    addCharacterSkills: builder.mutation({
      query: (data) => ({
        url: '/skills-add/',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Character', 'Skills'], // добавлен 'Skills'
    }),        

    getMyInfo: builder.query({
      query: () => ({ url: '/my-info', method: 'GET' }),
      providesTags: ['CharacterInfo'],
    }),

    updateMyInfo: builder.mutation({
      query: ({ infoId, infoData }) => ({
        url: `/my-info/${infoId}`,
        method: 'PUT',
        data: infoData,
      }),
      invalidatesTags: ['CharacterInfo'],
    }),

    getSimpleCharacterByName: builder.query({
      query: (characterName) => ({
        url: `/name/${characterName}/simple`,
        method: 'GET',
      }),
      // Кэш не держим долго, это разовый поиск
      keepUnusedDataFor: 10, 
    }),
        
    getAppliedSkills: builder.query({
      query: () => ({ url: '/applied-skills/', method: 'GET' }),
      providesTags: ['AppliedSkills'],
      keepUnusedDataFor: 300,
    }),
    
    calculateSkillsCost: builder.mutation({
      query: (data) => ({ 
        url: '/skills-calculate/', 
        method: 'POST', 
        data // { step: number, skill_type: "standard" | "mastership" }
      }),
    }),
   
    updateCharacterSkills: builder.mutation({
      query: (data) => ({
        url: '/skills-update/',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Character', 'Skills', 'AppliedSkills'], 
    }),

    changeLocation: builder.mutation({
      query: (locationSlug) => ({
        url: `/locations/${locationSlug}`,
        method: 'POST',
      }),
      // Character не инвалидируем: ответ мутации эквивалентен GET /only-me
      // (тот же CharacterReadSchema) и атомарно пишется в кэш getOnlyMe
      // в коммите перехода. Лишний refetch после каждого перехода не нужен.
    }),

    getSimpleMe: builder.query({
      query: () => ({
        url: '/simple/me',
        method: 'GET',
        skipAuthRetry: true, // 401 не запускает refresh-цепочку (публичная страница)
      }),
      keepUnusedDataFor: 5 * 60,
    }),

    getMyCharacters: builder.query({
      query: () => ({ url: '/me', method: 'GET' }),
      providesTags: ['MyCharacters'],
    }),

    getCharacterCreationStatus: builder.query({
      query: () => ({ url: '/users/character-creation-status', method: 'GET' }),
      providesTags: ['CreationStatus'],
    }),

    checkHasDetachedCharacters: builder.query({
      query: () => ({ url: '/detach', method: 'GET' }),
      providesTags: ['DetachedStatus'],
    }),

        // ═══ QUERIES (чтение) ═══
    
    getAttachmentSettings: builder.query({
      query: () => ({ 
        url: '/attachment-settings', 
        method: 'GET' 
      }),
      // Можно добавить тег, если эти настройки меняются редко, 
      // но пока оставим без тега для простоты, или добавим ['AttachmentSettings'] в tagTypes
    }),
    

    getDetachedCharacters: builder.query({
      query: () => ({ 
        url: '/detach/all', 
        method: 'GET' 
      }),
      providesTags: ['DetachedCharacters'],
    }),

    // ══ MUTATIONS (изменения) ═══

    detachCharacter: builder.mutation({
      query: (characterId) => ({
        url: `/detach/${characterId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['MyCharacters', 'CreationStatus', 'DetachedCharacters', 'DetachedStatus'],
    }),

    attachCharacter: builder.mutation({
      query: ({ id }) => ({
        url: `/attach/${id}`,
        method: 'POST',
      }),
      invalidatesTags: ['MyCharacters', 'CreationStatus', 'DetachedCharacters', 'DetachedStatus'],
    }),

    getTransferRules: builder.query({
      query: () => ({ 
        url: '/transfer/rules', 
        method: 'GET' 
      }),
      providesTags: ['TransferRules'],
    }),

    transferCurrency: builder.mutation({
      query: (transferData) => ({
        url: '/transfer',
        method: 'POST',
        data: transferData,
      }),
      // После успешного перевода балансы у обоих персонажей меняются — обновляем список
      invalidatesTags: ['MyCharacters', 'Character'],
    }),

    createCharacter: builder.mutation({
      query: (characterData) => ({
        url: '/',
        method: 'POST',
        data: characterData,
      }),
      invalidatesTags: ['MyCharacters', 'CreationStatus'],
    }),

    getReferralLink: builder.query({
      query: () => ({ 
        url: '/referral-link', 
        method: 'GET' 
      }),
      providesTags: ['ReferralLink'],
    }),

    getCharacterByName: builder.query({
      query: (characterName) => ({
        url: `/name/${characterName}/info`,
        method: 'GET',
      }),
      keepUnusedDataFor: 60,
    }),

    getCharacter: builder.query({
      query: (characterId) => ({
        url: `/${characterId}`,
        method: 'GET',
      }),
      providesTags: (result, error, id) => 
        result ? [{ type: 'CharacterFull', id }] : [],
      keepUnusedDataFor: 60,
    }),

    
  }),
});

export const {
  useGetOnlyMeQuery,
  useGetCharacterSkillsQuery,
  useGetLocationsStatsQuery,
  useGetAppliedSkillsQuery,
  useCalculateSkillsCostMutation,
  useUpdateCharacterSkillsMutation,
  useAddCharacterSkillsMutation,
  useGetMyInfoQuery,
  useUpdateMyInfoMutation,
  useLazyGetSimpleCharacterByNameQuery,
  useChangeLocationMutation,
  useGetSimpleMeQuery,
  useGetMyCharactersQuery,
  useGetCharacterCreationStatusQuery,
  useCheckHasDetachedCharactersQuery,
  useGetAttachmentSettingsQuery,
  useDetachCharacterMutation,
  useGetDetachedCharactersQuery,
  useAttachCharacterMutation,
  useGetTransferRulesQuery,
  useTransferCurrencyMutation,
  useCreateCharacterMutation,
  useGetReferralLinkQuery,
  useLazyGetCharacterByNameQuery,
  useGetCharacterQuery,
} = characterApi;
import { createApi } from '@reduxjs/toolkit/query/react';
import { captchaApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

/**
 * Два независимых слайса над одним POST /captcha:
 *
 * 1. captchaApi (query) — мастерская и майнинг: кэшируется, гейт локации
 *    дожидает (required: true в defaultViewPrefetches), таймерный префетч
 *    перед финишем кладёт свежую в кэш, расход — invalidateTags(['Captcha']).
 *    НЕ использовать на публичных страницах.
 *
 * 2. captchaMutationApi (mutation) — RegisterPage: одноразовый вызов без кэша.
 *    НЕ использовать в мастерской и майнинге.
 */
export const captchaApi = createApi({
  reducerPath: 'captchaApi',
  baseQuery: createAxiosBaseQuery(captchaApiInstance),
  endpoints: (builder) => ({
    getCaptcha: builder.query({
      query: () => ({ url: '/', method: 'POST' }),
      providesTags: ['Captcha'],
      keepUnusedDataFor: 300,
    }),
  }),
});

export const { useGetCaptchaQuery } = captchaApi;

// ═══ Отдельный слайс-мутация (без кэша) ═══
export const captchaMutationApi = createApi({
  reducerPath: 'captchaMutationApi',
  baseQuery: createAxiosBaseQuery(captchaApiInstance),
  endpoints: (builder) => ({
    getCaptcha: builder.mutation({
      query: () => ({ url: '/', method: 'POST' }),
    }),
  }),
});

export const { useGetCaptchaMutation } = captchaMutationApi;
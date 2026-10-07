// src/services/visitService.js
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import { visitApiInstance } from '../api/axiosInstance';

class VisitService {
  constructor() {
    this.fpPromise = null;           // Промис для FingerprintJS
    this.fingerprintCache = null;    // ✅ Кеш самого fingerprint
    this.visitResultCache = null;    // ✅ Кеш результата визита
    this.visitPromise = null;        // ✅ Промис запроса (от race condition)
  }

  // Инициализация FingerprintJS (вызывается один раз)
  async initFingerprint() {
    if (!this.fpPromise) {
      this.fpPromise = FingerprintJS.load();
    }
    return this.fpPromise;
  }

  // Генерация fingerprint с кешированием
  async generateFingerprint() {
    // ✅ Если уже сгенерирован, возвращаем из кеша
    if (this.fingerprintCache) {
      return this.fingerprintCache;
    }

    try {
      const fp = await this.initFingerprint();
      const result = await fp.get();
      this.fingerprintCache = result.visitorId;
      return this.fingerprintCache;
    } catch (error) {
      console.error('Error generating fingerprint:', error);
      // Fallback на простой fingerprint
      this.fingerprintCache = this.getFallbackFingerprint();
      return this.fingerprintCache;
    }
  }

  // Fallback fingerprint если основная библиотека не работает
  getFallbackFingerprint() {
    const ua = navigator.userAgent;
    const screen = `${window.screen.width}x${window.screen.height}`;
    const language = navigator.language;
    const platform = navigator.platform;
    
    const data = `${ua}|${screen}|${language}|${platform}`;
    
    // Простой hash
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  }

  // Извлечение referral_name из URL
  getReferralName() {
    const urlParams = new URLSearchParams(window.location.search);
    const ref = urlParams.get('ref');
    return ref || null;
  }

  // ✅ Публичный метод для получения fingerprint (если нужен отдельно)
  async getFingerprint() {
    return await this.generateFingerprint();
  }

  // Основной метод для отправки визита
  async visit(customData = {}) {
    // ✅ Защита от race condition: если запрос уже идёт
    if (this.visitPromise) {
      console.log('Visit request already in progress, reusing promise');
      return this.visitPromise;
    }

    // ✅ Если визит уже был, возвращаем закешированный результат
    if (this.visitResultCache) {
      console.log('Visit already tracked, returning cached result');
      return this.visitResultCache;
    }

    // Создаём промис и кешируем его
    this.visitPromise = this._performVisit(customData);

    try {
      const result = await this.visitPromise;
      this.visitResultCache = result; // ✅ Кешируем результат
      return result;
    } finally {
      this.visitPromise = null; // Очищаем промис после завершения
    }
  }

  // Внутренний метод для выполнения запроса
  async _performVisit(customData) {
    try {
      const fingerprint = await this.generateFingerprint();
      const refferal_name = this.getReferralName();

      const data = {
        fingerprint,
        refferal_name,
        ...customData,
      };

      let response;
      try {
        response = await visitApiInstance.post('/', data);
      } catch (error) {
        console.error('Auth check error:', error);
        throw error;
      }
      const result = response.data;
      return result;
    } catch (error) {
      console.error('Error tracking visit:', error);
      throw error;
    }
  }

  // ✅ Метод для сброса кешей (полезен для тестирования)
  reset() {
    this.fingerprintCache = null;
    this.visitResultCache = null;
    this.visitPromise = null;
    // fpPromise оставляем, т.к. FingerprintJS можно переиспользовать
  }

  // ✅ Получить visit_id из кеша (для использования в регистрации)
  getVisitId() {
    return this.visitResultCache?.id || null;
  }
}

export default new VisitService();
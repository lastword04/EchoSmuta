import { describe, it, expect } from 'vitest';
import { 
  getBaseEconomyInvalidationTags, 
  getEconomyResyncInvalidationTags 
} from '../../../shared/config/websocketEvents/invalidateOnEconomyEvent';

describe('invalidateOnEconomyEvent', () => {
  describe('getBaseEconomyInvalidationTags', () => {
    it('возвращает правильные теги для базовой инвалидации', () => {
      const tags = getBaseEconomyInvalidationTags();
      
      expect(tags).toEqual({
        characterApi: ['Character'],
        economyApi: ['Economy', 'Lots', 'Market', 'Resources'],
        resourcesApi: ['Resources', 'MiningStatus', 'Economy'],
        inventoryApi: ['StartedCrafting', 'WorkshopRecipes'],
      });
    });

    it('возвращает новый объект при каждом вызове (защита от мутаций)', () => {
      const tags1 = getBaseEconomyInvalidationTags();
      const tags2 = getBaseEconomyInvalidationTags();
      
      expect(tags1).not.toBe(tags2);
      expect(tags1).toEqual(tags2);
    });
  });

  describe('getEconomyResyncInvalidationTags', () => {
    it('возвращает правильные теги для массовой инвалидации', () => {
      const tags = getEconomyResyncInvalidationTags();
      
      expect(tags.characterApi).toEqual(['Character', 'LocationsStats']);
      expect(tags.economyApi).toEqual(['Economy', 'Lots', 'Market']);
      expect(tags.resourcesApi).toEqual(['Resources', 'MiningStatus', 'Economy']);
      expect(tags.inventoryApi).toContain('Inventory');
      expect(tags.inventoryApi).toContain('ShopsList');
      expect(tags.chatApi).toEqual(['OnlineUsers']);
    });
  });
});
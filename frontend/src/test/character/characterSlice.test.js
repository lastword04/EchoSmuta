import { describe, it, expect } from 'vitest';

import characterReducer, {
  applySnapshot,
  applyVolatile,
  setLocation,
  commitLocation,
  selectCharacter,
  clearVolatile,
} from '../../entities/character/store/characterSlice';
import {
  clearActiveCharacterId,
  setActiveCharacterId,
} from '../../shared/store/activeCharacterIdSlice';

const FRESH = {
  id: 1, name: 'Hero', level: 5, location_slug: 'forest',
  health: 100, mana: 50, tiredness: 1.5, equipment_bonuses: { a: 1 },
  effective_power: 10, effective_agility: 10, effective_lucky: 10,
  effective_max_health: 100, effective_max_mana: 50, effective_max_tiredness: 5,
};

const initial = characterReducer(undefined, { type: '@@INIT' });
const run = (state, action) => characterReducer(state, action);
const assembled = (state) => selectCharacter({ character: state });

describe('characterSlice (variant C)', () => {
  it('первый снапшот ждёт баффы, если они ещё грузятся', () => {
    expect(run(initial, applySnapshot({ character: FRESH, buffsIsFetching: true }))).toBe(initial);
  });

  it('первый снапшот применяется полностью', () => {
    const s = run(initial, applySnapshot({ character: FRESH, buffs: [{ id: 'b1' }] }));
    const c = assembled(s);
    expect(c.id).toBe(1);
    expect(c.buffs).toEqual([{ id: 'b1' }]);
    expect(c.location_slug).toBe('forest'); // fallback на snapshot, коммитов ещё не было
  });

  it('REST-рефетч НЕ перетирает volatile и location на чтении', () => {
    let s = run(initial, applySnapshot({ character: FRESH, buffs: [] }));
    s = run(s, applyVolatile({ health: 42, mana: 7 }));
    s = run(s, setLocation('tavern'));

    // свежий REST со старыми volatile
    const stale = { ...FRESH, level: 6, health: 100, mana: 50, location_slug: 'forest' };
    s = run(s, applySnapshot({ character: stale }));

    const c = assembled(s);
    expect(c.level).toBe(6);              // статика обновилась
    expect(c.health).toBe(42);            // volatile от WS
    expect(c.mana).toBe(7);
    expect(c.location_slug).toBe('tavern'); // location от перехода
  });

  it('applyVolatile игнорирует служебные ключи и null (partial payload)', () => {
    let s = run(initial, applySnapshot({ character: FRESH, buffs: [] }));
    s = run(s, applyVolatile({ event: 'stats_updated', health: 33, mana: 44, effective_power: null }));

    const c = assembled(s);
    expect(c.health).toBe(33);
    expect(c.mana).toBe(44);
    expect(c.effective_power).toBe(FRESH.effective_power); // null не сбросил
    expect(c.event).toBeUndefined();                        // служебный ключ не протёк
  });

  it('commitLocation фиксирует локацию и сохраняет volatile', () => {
    let s = run(initial, applySnapshot({ character: FRESH, buffs: [] }));
    s = run(s, applyVolatile({ health: 12 }));
    s = run(s, commitLocation({ locationSlug: 'mine', character: { ...FRESH, location_slug: 'mine', level: 6 } }));

    const c = assembled(s);
    expect(c.location_slug).toBe('mine');
    expect(c.health).toBe(12);
    expect(c.level).toBe(6); // статика из ответа мутации
  });

  it('clearVolatile очищает только volatile (snapshot и locationSlug целы)', () => {
    let s = run(initial, applySnapshot({ character: FRESH, buffs: [{ id: 'b1' }] }));
    s = run(s, applyVolatile({ health: 42, mana: 7, effective_power: 99 }));
    s = run(s, setLocation('tavern'));

    s = run(s, clearVolatile());

    expect(s.volatile).toEqual({});        // volatile очищен
    expect(s.snapshot).toEqual(FRESH);     // snapshot не тронут
    expect(s.locationSlug).toBe('tavern'); // локация не тронута

    // На чтении volatile-поля берутся из snapshot (fallback), локация — из корзины
    const c = assembled(s);
    expect(c.health).toBe(FRESH.health);
    expect(c.mana).toBe(FRESH.mana);
    expect(c.effective_power).toBe(FRESH.effective_power);
    expect(c.location_slug).toBe('tavern');
  });

  it('сбрасывается на логауте и на смене персонажа', () => {
    const s = run(initial, applySnapshot({ character: FRESH, buffs: [] }));
    expect(run(s, clearActiveCharacterId())).toEqual(initial);
    expect(run(s, setActiveCharacterId(999))).toEqual(initial);
    expect(run(s, setActiveCharacterId(1))).toBe(s); // тот же id — no-op
  });
});
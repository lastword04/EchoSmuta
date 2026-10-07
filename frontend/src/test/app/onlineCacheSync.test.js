// Unit-тест draft-логики onlineCacheSync.
//
// Подход: API-слайсы мокаются (как в test/chat/cacheInvalidation.test.js), поэтому
// сети нет. Мок `util.updateQueryData` возвращает объект-действие
// { endpointName, args, updater }, который перехватывает dispatch. Затем updater
// применяется к черновику через produce (Immer) — ровно так, как это делает
// RTK Query внутри редьюсера. Это позволяет проверять сами мутации draft,
// не поднимая настоящий store/сеть.
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { produce } from 'immer';

vi.mock('../../entities/chat/api/chatApi', () => ({
  chatApi: {
    util: {
      updateQueryData: vi.fn((endpointName, args, updater) => ({ endpointName, args, updater })),
    },
  },
}));

vi.mock('../../entities/character/api/characterApi', () => ({
  characterApi: {
    util: {
      updateQueryData: vi.fn((endpointName, args, updater) => ({ endpointName, args, updater })),
    },
  },
}));

import {
  moveOnlineUser,
  setOnlineUserPresence,
  ONLINE_PAGE_LIMIT,
  ONLINE_PAGE_OFFSET,
} from '../../app/providers/lib/onlineCacheSync';
import { chatApi } from '../../entities/chat/api/chatApi';
import { characterApi } from '../../entities/character/api/characterApi';

const GLOBAL_KEY = 'global';

const globalArgs = { locationSlug: null, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET };
const locationArgs = (slug) => ({ locationSlug: slug, limit: ONLINE_PAGE_LIMIT, offset: ONLINE_PAGE_OFFSET });

// --- Сид кэшей RTK Query: global + две локации + статистика ---

const createWorld = () => ({
  online: {
    global: {
      objects: [
        { id: 1, name: 'Hero', location_slug: 'forest' },
        { id: 2, name: 'Bob', location_slug: 'tavern' },
      ],
      count: 2,
    },
    forest: {
      objects: [{ id: 1, name: 'Hero', location_slug: 'forest' }],
      count: 1,
    },
    tavern: {
      objects: [{ id: 2, name: 'Bob', location_slug: 'tavern' }],
      count: 1,
    },
  },
  stats: [
    { location_slug: 'forest', count: 1 },
    { location_slug: 'tavern', count: 1 },
  ],
});

// Перехватываем действия, которые модуль передаёт в dispatch
const captureDispatch = () => {
  const actions = [];
  const dispatch = vi.fn((action) => {
    actions.push(action);
    return action;
  });
  return { dispatch, actions };
};

// Применяем перехваченные updater'ы к черновику (как реальный RTK Query)
const applyActions = (world, actions) => {
  for (const action of actions) {
    if (action.endpointName === 'getOnlineCharacters') {
      const key = action.args.locationSlug ?? GLOBAL_KEY;
      world.online[key] = produce(world.online[key], (draft) => action.updater(draft));
    } else if (action.endpointName === 'getLocationsStats') {
      world.stats = produce(world.stats, (draft) => action.updater(draft));
    } else {
      throw new Error(`Неожиданный endpoint в тесте: ${action.endpointName}`);
    }
  }
};

const findById = (cache, id) => cache.objects.find((u) => u.id === id);

beforeEach(() => {
  chatApi.util.updateQueryData.mockClear();
  characterApi.util.updateQueryData.mockClear();
});


describe('moveOnlineUser', () => {
  it('переносит пользователя: global обновлён, старая -1, новая +1, статистика сдвинута', () => {
    const world = createWorld();
    const { dispatch, actions } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug: 'forest',
      newLocationSlug: 'tavern',
      userData: { id: 1, name: 'Hero', location_slug: 'forest' },
    });

    expect(dispatch).toHaveBeenCalledTimes(4);
    applyActions(world, actions);

    // global: location_slug обновлён, count не изменился (пользователь там уже был)
    expect(findById(world.online.global, 1).location_slug).toBe('tavern');
    expect(world.online.global.count).toBe(2);

    // старая локация: пользователь удалён, count декрементирован
    expect(world.online.forest.objects).toHaveLength(0);
    expect(world.online.forest.count).toBe(0);

    // новая локация: пользователь добавлен с новой локацией, count инкрементирован
    expect(world.online.tavern.objects.map((u) => u.id)).toEqual([1, 2]);
    expect(world.online.tavern.objects[0]).toMatchObject({ id: 1, location_slug: 'tavern' });
    expect(world.online.tavern.count).toBe(2);

    // статистика: -1 старая, +1 новая
    expect(world.stats).toEqual([
      { location_slug: 'forest', count: 0 },
      { location_slug: 'tavern', count: 2 },
    ]);
  });

  it('использует ключи кэша ONLINE_PAGE_LIMIT/OFFSET и правильные locationSlug', () => {
    const { dispatch, actions } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug: 'forest',
      newLocationSlug: 'tavern',
      userData: { id: 1, name: 'Hero', location_slug: 'forest' },
    });

    const [globalAction, oldAction, newAction, statsAction] = actions;

    expect(globalAction.endpointName).toBe('getOnlineCharacters');
    expect(globalAction.args).toEqual(globalArgs);

    expect(oldAction.args).toEqual(locationArgs('forest'));
    expect(newAction.args).toEqual(locationArgs('tavern'));

    expect(statsAction.endpointName).toBe('getLocationsStats');
    expect(statsAction.args).toBeUndefined();
  });

  it('идемпотентен: повторный upsert в новую локацию не создаёт дубликат и не меняет count', () => {
    const world = createWorld();
    // presence уже успел добавить Hero в tavern до перехода
    world.online.tavern = {
      objects: [{ id: 1, name: 'Hero', location_slug: 'tavern' }, ...world.online.tavern.objects],
      count: 2,
    };
    const { dispatch, actions } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug: 'forest',
      newLocationSlug: 'tavern',
      userData: { id: 1, name: 'Hero', location_slug: 'forest' },
    });
    applyActions(world, actions);

    expect(world.online.tavern.objects.filter((u) => u.id === 1)).toHaveLength(1);
    expect(world.online.tavern.count).toBe(2);
  });

  it.each([
    ['undefined', undefined],
    ['null', null],
    ['пустая строка', ''],
  ])('no-op при пустом oldLocationSlug (%s)', (_label, oldLocationSlug) => {
    const { dispatch } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug,
      newLocationSlug: 'tavern',
      userData: { id: 1, name: 'Hero' },
    });

    expect(dispatch).not.toHaveBeenCalled();
  });

  it('no-op, если oldLocationSlug === newLocationSlug', () => {
    const { dispatch } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug: 'tavern',
      newLocationSlug: 'tavern',
      userData: { id: 1, name: 'Hero' },
    });

    expect(dispatch).not.toHaveBeenCalled();
  });

  it('no-op без userData', () => {
    const { dispatch } = captureDispatch();

    moveOnlineUser(dispatch, {
      characterId: 1,
      oldLocationSlug: 'forest',
      newLocationSlug: 'tavern',
      userData: undefined,
    });

    expect(dispatch).not.toHaveBeenCalled();
  });
});

describe('setOnlineUserPresence', () => {
  it('online=true: upsert в global и location, +1 в статистике', () => {
    const world = createWorld();
    const { dispatch, actions } = captureDispatch();

    setOnlineUserPresence(dispatch, {
      characterId: 30,
      isOnline: true,
      locationSlug: 'tavern',
      userData: { id: 30, name: 'Carol' }, // без location_slug — модуль сам проставит его
    });

    expect(dispatch).toHaveBeenCalledTimes(3);
    applyActions(world, actions);

    // global: добавлен в начало, count +1
    expect(world.online.global.count).toBe(3);
    expect(world.online.global.objects[0]).toMatchObject({ id: 30, name: 'Carol', location_slug: 'tavern' });

    // локация: добавлен, count +1
    expect(world.online.tavern.count).toBe(2);
    expect(findById(world.online.tavern, 30)).toMatchObject({ location_slug: 'tavern' });

    // статистика: +1 в tavern
    expect(world.stats).toEqual([
      { location_slug: 'forest', count: 1 },
      { location_slug: 'tavern', count: 2 },
    ]);
  });

  it('online=false: remove из global и location, -1 в статистике', () => {
    const world = createWorld();
    world.online.global = {
      objects: [...world.online.global.objects, { id: 30, name: 'Carol', location_slug: 'tavern' }],
      count: 3,
    };
    world.online.tavern = {
      objects: [...world.online.tavern.objects, { id: 30, name: 'Carol', location_slug: 'tavern' }],
      count: 2,
    };
    world.stats = [
      { location_slug: 'forest', count: 1 },
      { location_slug: 'tavern', count: 2 },
    ];
    const { dispatch, actions } = captureDispatch();

    setOnlineUserPresence(dispatch, {
      characterId: 30,
      isOnline: false,
      locationSlug: 'tavern',
    });

    expect(dispatch).toHaveBeenCalledTimes(3);
    applyActions(world, actions);

    // global: удалён, count -1
    expect(world.online.global.count).toBe(2);
    expect(findById(world.online.global, 30)).toBeUndefined();

    // локация: удалён, count -1
    expect(world.online.tavern.count).toBe(1);
    expect(findById(world.online.tavern, 30)).toBeUndefined();

    // статистика: -1 в tavern
    expect(world.stats).toEqual([
      { location_slug: 'forest', count: 1 },
      { location_slug: 'tavern', count: 1 },
    ]);
  });

  it.each([
    ['undefined', undefined],
    ['null', null],
  ])('online=true без userData (%s) → no-op', (_label, userData) => {
    const { dispatch } = captureDispatch();

    setOnlineUserPresence(dispatch, {
      characterId: 30,
      isOnline: true,
      locationSlug: 'tavern',
      userData,
    });

    expect(dispatch).not.toHaveBeenCalled();
  });
});


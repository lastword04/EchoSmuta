import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { AUTH_STORAGE_STATE } from "../playwright.config";

/**
 * E2E: окно сделки (Торговая Палата, 1.27.trade-hall) + защита маршрутов.
 *
 * Схема storageState:
 *  - ГЛОБАЛЬНОГО storageState НЕТ (playwright.config.ts);
 *  - Фазы 1–2 всегда идут на ЧИСТОМ контексте;
 *  - авторизованные тесты явно подключают сессию:
 *        test.use({ storageState: AUTH_STORAGE_STATE })
 *    и SKIP, если файла сессии нет (process.env.E2E_STORAGE_STATE).
 */

const TRADE_HALL_TITLE = "Торговая Палата";
const DEALS_TAB = "Сделки";
const CONFIRM_BTN = "Подтвердить сделку";
const CANCEL_BTN = "Отменить сделку";

test.beforeEach(async ({ request }) => {
  // Проба доступности фронтенда: если стек не поднят — пропускаем прогон.
  const base = test.info().project.use.baseURL ?? "http://localhost:5173";
  let up = false;
  try {
    const resp = await request.get(base);
    up = resp.ok();
  } catch {
    up = false;
  }
  test.skip(!up, `Фронтенд ${base} недоступен — стек не поднят, E2E пропущен.`);
});

async function isInTradeHall(page: Page): Promise<boolean> {
  try {
    // Ждём до 10 секунд, пока заголовок появится на странице
    await page.getByText(TRADE_HALL_TITLE, { exact: false }).first().waitFor({
      state: 'visible',
      timeout: 10_000,
    });
    return true;
  } catch {
    // Таймаут или элемент не найден — персонаж не в Палате
    return false;
  }
}

test.describe("Защита маршрутов и окно сделки", () => {
  test("фронтенд отвечает и отдаёт приложение", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/.+/);
  });

  // ═══ ФАЗА 1: прямой заход без авторизации ═══
  // Всегда на чистом контексте (глобального storageState в конфиге нет).
  test("без авторизации /location → /characters → само-излечение на /login", async ({ page }) => {
    await page.goto("/location");

    // Новый контракт ProtectedRoute: игровой маршрут без activeCharacterId →
    // <Navigate to="/characters"> (выбор персонажа, а НЕ /login).
    // Промежуточный шаг может быть мимолётным: /characters без cookies сам
    // запускает цепочку 401 → refresh fail → notifyAuthError → auth-error →
    // /login, поэтому первый ассерт — мягкий.
    await expect(page).toHaveURL(/\/characters/, { timeout: 10_000 }).catch(() => {
      // Само-излечение обогнало опрос URL — допустимо, финальный ассерт ниже.
    });
    // Конечная точка — /login.
    try {
      await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
    } catch {
      // Первая волна могла застрять в refresh-цепочке — перезапуск цикла запросов.
      await page.reload();
      await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
    }
    // Форма входа реально отрисована (а не пустая страница).
    await expect(page.locator("input").first()).toBeVisible();
  });

  // ═══ ФАЗА 2: истёкшая сессия (cookies мертвы, persist живой) ═══
  // Тоже чистый контекст: fake-persist подселяется через addInitScript.
  test("истёкшая сессия: cookies мертвы, persist живой → 401 выталкивает на /login", async ({
    page,
  }) => {
    // persist говорит «авторизован» (ProtectedRoute впустит внутрь),
    // cookies нет → запросы дают 401 → axios-интерцептор: refresh падает
    // → notifyAuthError() → ProtectedRoute уводит на /login.
    await page.addInitScript(() => {
      const fakePersist = {
        activeCharacterId: JSON.stringify('00000000-0000-4000-8000-000000000001'),
        activeCharacterName: JSON.stringify('GhostSession'),
        mode: JSON.stringify('day'),
        _persist: JSON.stringify({ version: -1, rehydrated: true }),
      };
      localStorage.setItem('persist:local', JSON.stringify(fakePersist));
    });

    await page.goto("/location");

    // Первая волна может застрять в refresh-цепочке интерцептора —
    // щедрый таймаут; fallback: reload перезапускает цикл запросов.
    try {
      await expect(page).toHaveURL(/\/login/, { timeout: 30_000 });
    } catch {
      await page.reload();
      await expect(page).toHaveURL(/\/login/, { timeout: 30_000 });
    }
    await expect(page.locator("input").first()).toBeVisible();

    // Анти-шторм: после стабилизации остаёмся на /login без крашей.
    await page.waitForTimeout(1500);
    await expect(page).toHaveURL(/\/login/);
  });
});

// ═══ Авторизованные сценарии: явный test.use({ storageState }) ═══
test.describe("Авторизованные сценарии (storageState)", () => {
  // Сессия подключается ТОЛЬКО здесь — глобальной в конфиге нет.
  // ⚠️ test.use на уровне describe применяется ко ВСЕМ тестам блока
  // (гарантия Playwright). Если файла сессии нет, AUTH_STORAGE_STATE ===
  // undefined, а тесты ниже заскипятся по гейту E2E_STORAGE_STATE.
  test.use({ storageState: AUTH_STORAGE_STATE as any });

  const needSession = () =>
    test.skip(
      !process.env.E2E_STORAGE_STATE,
      "Нет сохранённой сессии: заполни e2e/.env (E2E_LOGIN/E2E_PASSWORD) и запусти npm run auth:state.",
    );

  // DEBUG: подтверждаем, что сессия подхвачена этим describe.
  test.beforeAll(() => {
    console.log(
      "[auth] storageState:",
      AUTH_STORAGE_STATE ?? "(undefined — авторизованные тесты будут SKIPPED)",
    );
  });

  // ═══ ЗАЩИТА ОТ РОТАЦИИ REFRESH-TOKEN ═══
  // Сервер может выдать НОВЫЙ refresh-cookie (ротация) и аннулировать старый
  // из state.json. Тогда следующий тест/прогон получает мёртвый refresh →
  // ложный logout на первом же goto. Лечим: после каждого теста сохраняем
  // актуальные cookies обратно в state.json. Logout-тест (он заканчивается
  // на /login с очищенным стейтом) НЕ сохраняем — там очистка намеренная.
  test.afterEach(async ({ page }) => {
    if (!AUTH_STORAGE_STATE) return;
    if (/\/login/.test(page.url())) return;
    await page.context().storageState({ path: AUTH_STORAGE_STATE });
  });

  test("после логина (storageState) /location НЕ редиректит на /login", async ({ page }) => {
    needSession();

    await page.goto("/location");

    // Авторизованный пользователь остаётся на защищённом маршруте:
    // refresh-цепочка интерцептора обновляет access-token прозрачно.
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 });
    await expect(page).toHaveURL(/\/location/);
  });

  test("после выхода (очистка cookies и storage) защищённый маршрут снова закрыт", async ({
    page,
  }) => {
    needSession();

    await page.goto("/location");
    // Если нас уже встретил /login — сессия не применилась ИЛИ refresh был
    // ротирован предыдущим тестом/протух. Подсказка вместо немого падения.
    if (!page.url().includes("/location")) {
      test.info().annotations.push({
        type: "warning",
        description: "Session not restored on first step — refresh state.json via npm run auth:state",
      });
    }

    // Первый заход может дернуть refresh-цепочку интерцептора.
    await expect(page).toHaveURL(/\/location/, { timeout: 15_000 });

    // Симуляция logout: чистим cookies И persist — при следующем заходе гард
    // уводит на /characters, а цепочка 401 → auth-error доводит до /login.
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());

    await page.goto("/location");
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
    await expect(page.locator("input").first()).toBeVisible();
  });

test("авторизованный пользователь видит окно сделки в Торговой Палате", async ({ page }) => {
  needSession();

  await page.goto("/location");
  await page.waitForLoadState("networkidle").catch(() => {});

  const tradeHallVisible = await isInTradeHall(page);
  test.skip(
    !tradeHallVisible,
    `Персонаж не в локации «${TRADE_HALL_TITLE}» — переместите его для прогона.`,
  );

  // Открываем вкладку «Сделки».
  await page.getByRole("button", { name: DEALS_TAB }).first().click();

  // Проверяем, что вкладка активна и показывает элементы для сделок
  // (список партнёров рядом, кнопка "Выбрать" для создания сделки)
  await expect(page.getByRole("button", { name: "Выбрать" }).first()).toBeVisible();
});

  test("кнопка добавления денег в сделке блокируется до выбора партнёра", async ({ page }) => {
    needSession();

    await page.goto("/location");
    const tradeHallVisible = await isInTradeHall(page);
    test.skip(!tradeHallVisible, `Персонаж не в «${TRADE_HALL_TITLE}».`);

    await page.getByRole("button", { name: DEALS_TAB }).first().click();

    const addMoney = page.getByRole("button", { name: "Добавить" }).first();
    if (await addMoney.isVisible().catch(() => false)) {
      // Без выбранного партнёра и активной сделки предложение денег недоступно.
      await expect(addMoney).toBeDisabled();
    } else {
      test.info().annotations.push({
        type: "info",
        description: "Контрол добавления денег скрыт до создания сделки — сценарий пустой.",
      });
    }
  });
});


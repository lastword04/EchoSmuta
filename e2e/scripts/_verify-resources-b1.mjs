#!/usr/bin/env node
/**
 * _verify-resources-b1.mjs
 * ---------------------------------------------------------------------------
 * E2E verification of the B1-resources fix.
 *
 * B1-resources: «капча сжигалась до проверки конфликта 409».
 * Fix (уже применён и проверен на диске):
 *   - resources/services/mining_actions.py: validate_captcha_and_mine делает ТОЛЬКО
 *     exists-check (409) + делегирование в creator с параметром captcha;
 *   - create_mining_action вызывает verify_captcha ПОСЛЕ проверок level/tiredness,
 *     непосредственно перед repository.create (insert).
 *
 * Следовательно `verify_captcha` (а значит и сжигание ключа капчи) вызывается ТОЛЬКО
 * после прохода 409 — активная добыча не «съедает» решённую капчу.
 *
 * Сценарии T1–T6 проверяют ровно это. Тестовый персонаж: БАН1
 * (id 84d932c3-f44e-4b9f-bb29-fc21fd1ef073).
 *
 * Инструменты: node:fetch (HTTP) + `docker exec redis redis-cli` для чтения кода
 * капчи и проверки TTL/живости ключа; `docker exec ... psql` для подготовки состояния
 * персонажа (перемещение на шахту с ресурсами — иначе celery-задача падает с
 * ValueError «all resurces not 100%» и action висит IN_PROGRESS → T4 невозможен).
 *
 * Замечание о кодах: POST /api/resources/mining/actions возвращает 200 (маршрут
 * зарегистрирован без status_code=201). Мы проверяем B1-инвариант через состояние
 * ключа капчи в Redis, а не через 201. Фактические коды фиксируются в отчёте.
 */
import { execSync } from 'child_process';

const AUTH = 'http://localhost:8080';
const CAP  = 'http://localhost:8089';
const MIN  = 'http://localhost:8088';
const CHAR_ID = '84d932c3-f44e-4b9f-bb29-fc21fd1ef073';
const REDIS_CONTAINER = 'redis';
const REDIS_PASS = 'redis_password';
const MINING_LOCATION = '2.2.shaft';
const ORIGINAL_LOCATION = '1.27.trade-hall';

// ---------------- helpers ----------------
function redis(args) {
  try {
    return execSync(
      `docker exec ${REDIS_CONTAINER} redis-cli --no-auth-warning -a ${REDIS_PASS} ${args}`,
      { encoding: 'utf8' }
    ).replace(/\s+$/, '');
  } catch (e) {
    return `ERR:${String(e.message).slice(0, 160)}`;
  }
}
const capKey = (id) => `captcha:${id}`;
const redisGet = (id) => { const v = redis(`GET "${capKey(id)}"`); return (v === '(nil)' || v === '') ? '' : v; };
const redisTtl  = (id) => redis(`TTL "${capKey(id)}"`);
const redisDel  = (id) => redis(`DEL "${capKey(id)}"`);

function dbPrep(sql) {
  return execSync(
    `docker exec character_service_db psql -U postgres -d character_service -v ON_ERROR_STOP=1 -c "${sql}"`,
    { encoding: 'utf8' }
  ).replace(/\s+$/, '');
}
function miningDb(sql) {
  return execSync(
    `docker exec mining_service_db psql -U postgres -d mining_service -v ON_ERROR_STOP=1 -c "${sql}"`,
    { encoding: 'utf8' }
  ).replace(/\s+$/, '');
}
const dbGetLocation = () =>
  execSync(`docker exec character_service_db psql -U postgres -d character_service -tAc "SELECT location_slug FROM characters WHERE id='${CHAR_ID}';"`, { encoding: 'utf8' }).replace(/\s+$/, '');

const JB = (obj) => Buffer.from(JSON.stringify(obj), 'utf8');

function jarFrom(resp) {
  const jar = {};
  let arr = resp.headers.getSetCookie ? resp.headers.getSetCookie() : [];
  // fallback: undici иногда склеивает Set-Cookie через ', ' (см. TEST_REPORT B3)
  if (arr.length === 0) {
    const raw = resp.headers.get('set-cookie');
    if (raw) arr = [raw];
  }
  for (const c of arr) {
    const kv = c.split(';')[0].trim();            // name=value
    const i = kv.indexOf('=');
    if (i > 0) jar[kv.slice(0, i).trim()] = kv.slice(i + 1).trim();
  }
  return jar;
}
let jar = {};
const api = (url, opts = {}) => {
  const headers = { ...(opts.headers || {}) };
  if (jar) headers['Cookie'] = Object.entries(jar).map(([k, v]) => `${k}=${v}`).join('; ');
  return fetch(url, { ...opts, headers });
};
const mergeCookies = (resp) => { jar = { ...jar, ...jarFrom(resp) }; };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (m) => console.log(m);
const fmt = (s, n = 240) => (s || '').slice(0, n);

const results = [];
function record(label, httpStatus, detail, pass) {
  results.push({ label, httpStatus, detail, pass });
  log(`\n[${pass ? 'PASS' : 'FAIL'}] ${label} | HTTP ${httpStatus} | ${detail}`);
}

// poll GET /api/resources/mining/status пока персонаж в деле (celery t+16..21с).
async function waitForMiningDone(timeoutSec = 200) {
  const deadline = Date.now() + timeoutSec * 1000;
  while (Date.now() < deadline) {
    await sleep(4000);
    const r = await api(`${MIN}/api/resources/mining/status`, { method: 'GET' });
    const j = await r.json().catch(() => ({}));
    log(`  poll: status=${j.status} id=${j.id ? j.id.slice(0, 8) : 'none'} remaining=${j.remaining_time_seconds ?? '—'}`);
    if (j.status === 'done' && !j.id) return true;
  }
  return false;
}

// ---------------- main ----------------
let originalLocation = ORIGINAL_LOCATION;
let ok = false;
const t0 = Date.now();
try {
  // PREP: перемещаем персонажа на шахту с ресурсами + чистим mining_actions
  log('=== PREP: DB state ===');
  originalLocation = dbGetLocation() || ORIGINAL_LOCATION;
  dbPrep(`UPDATE characters SET location_slug='${MINING_LOCATION}' WHERE id='${CHAR_ID}';`);
  miningDb(`DELETE FROM mining_actions WHERE character_id='${CHAR_ID}';`);
  log(`  char location -> ${MINING_LOCATION} (original: ${originalLocation})`);

  // AUTH: login + /play
  log('\n=== AUTH: login + /play ===');
  const login = await api(`${AUTH}/api/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ name: 'БАН1', password: '1', fingerprint: 'e2e-b1-resources' }),
  });
  mergeCookies(login);
  log(`  login HTTP ${login.status}`);
  const play = await api(`${AUTH}/api/auth/characters/${CHAR_ID}/play`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ fingerprint: 'e2e-b1-resources' }),
  });
  mergeCookies(play);
  const playBody = await play.json().catch(() => ({}));
  log(`  play HTTP ${play.status} | location=${playBody.location_slug} level=${playBody.level} tiredness=${playBody.tiredness}`);
  if (play.status !== 200) throw new Error(`play failed: ${play.status}`);

  // T1: старт добычи с верной капчей -> success, ключ удалён (сжигана после insert)
  log('\n=== T1: старт добычи с верной капчей (success + ключ удалён) ===');
  const c1 = await (await fetch(`${CAP}/api/captcha/`, { method: 'POST' })).json();
  const code1 = redisGet(c1.captcha_id);
  log(`  captcha ${c1.captcha_id.slice(0, 8)}… code=${code1} ttl=${redisTtl(c1.captcha_id)}`);
  const t1 = await api(`${MIN}/api/resources/mining/actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ captcha_id: c1.captcha_id, user_input: code1 }),
  });
  const t1Body = await t1.json().catch(() => ({}));
  const t1Key = redisGet(c1.captcha_id);
  log(`  T1 HTTP ${t1.status} | status=${t1Body.status} | redis key after = "${t1Key}"`);
  const t1Pass = (t1.status === 200 || t1.status === 201) && t1Body.status === 'in_progress' && t1Key === '';
  record('T1 старт добычи + верная капча', t1.status,
    t1Key === '' ? 'ключ удалён (сжигана после insert)' : 'ключ ЖИВ — B1 нарушен!', t1Pass);
  // T2: верная капча при активной добыче -> 409 (exists-check ДО verify_captcha)
  log('\n=== T2: верная капча при АКТИВНОЙ добыче (ожидается 409) ===');
  const c2 = await (await fetch(`${CAP}/api/captcha/`, { method: 'POST' })).json();
  const code2 = redisGet(c2.captcha_id);
  log(`  captcha ${c2.captcha_id.slice(0, 8)}… code=${code2} ttl=${redisTtl(c2.captcha_id)}`);
  const t2 = await api(`${MIN}/api/resources/mining/actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ captcha_id: c2.captcha_id, user_input: code2 }),
  });
  const t2Body = await t2.json().catch(() => ({}));
  log(`  T2 HTTP ${t2.status} | error_code=${t2Body.error_code}`);
  const t2Pass = t2.status === 409 && t2Body.error_code === 'RESOURCE_ALREADY_MINING';
  record('T2 верная капча при активной добыче', t2.status,
    `error_code=${t2Body.error_code || '?'}`, t2Pass);

  // T3: после 409 ключ капчи ЖИВ (TTL > 0) — главный инвариант B1
  log('\n=== T3: после 409 ключ капчи ЖИВ (TTL > 0) ===');
  const t3Key = redisGet(c2.captcha_id);
  const t3Ttl = redisTtl(c2.captcha_id);
  log(`  key="${t3Key}" (expect code2=${code2}) ttl=${t3Ttl}`);
  const t3Pass = t3Key === code2 && Number(t3Ttl) > 0;
  record('T3 ключ капчи жив после 409', 'n/a',
    `key_alive=${t3Key === code2} ttl=${t3Ttl}`, t3Pass);

  // ждём завершения добычи №1 (celery) — polling статуса, НЕ фиксируем sleep
  log('\n=== POLL: ждём завершения добычи №1 (celery, ~60с+) ===');
  const done1 = await waitForMiningDone(200);
  log(`  добыча #1 завершена: ${done1}`);
  if (!done1) throw new Error('mining #1 did not complete in time');

  // T4: после завершения ТА ЖЕ капча (c2) -> success, ключ удалён
  log('\n=== T4: после завершения ТА ЖЕ капча -> success + ключ удалён ===');
  const t4 = await api(`${MIN}/api/resources/mining/actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ captcha_id: c2.captcha_id, user_input: code2 }),
  });
  const t4Body = await t4.json().catch(() => ({}));
  const t4Key = redisGet(c2.captcha_id);
  log(`  T4 HTTP ${t4.status} | status=${t4Body.status} | redis key after = "${t4Key}"`);
  const t4Pass = (t4.status === 200 || t4.status === 201) && t4Body.status === 'in_progress' && t4Key === '';
  record('T4 ТА ЖЕ капча после завершения', t4.status,
    t4Key === '' ? 'ключ удалён (сжигана)' : 'ключ ЖИВ — B1 нарушен!', t4Pass);
  // ждём завершения добычи №2 (celery) — polling статуса, НЕ фиксируем sleep
  log('\n=== POLL: ждём завершения добычи №2 (celery) ===');
  const done2 = await waitForMiningDone(200);
  log(`  добыча #2 завершена: ${done2}`);
  if (!done2) throw new Error('mining #2 did not complete in time');

  // T5: неверный код -> 400, ключ жив (verify_captcha не сжигает при wrong input)
  log('\n=== T5: неверный код -> 400, ключ жив ===');
  const c3 = await (await fetch(`${CAP}/api/captcha/`, { method: 'POST' })).json();
  const code3 = redisGet(c3.captcha_id);
  log(`  captcha ${c3.captcha_id.slice(0, 8)}… code=${code3}`);
  const t5 = await api(`${MIN}/api/resources/mining/actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ captcha_id: c3.captcha_id, user_input: 'WRONG_CODE' }),
  });
  const t5Body = await t5.json().catch(() => ({}));
  const t5Key = redisGet(c3.captcha_id);
  log(`  T5 HTTP ${t5.status} | error_code=${t5Body.error_code} | redis key="${t5Key}" (expect ${code3})`);
  const t5Pass = t5.status === 400 && t5Body.error_code === 'INVALID_CAPTCHA_INPUT' && t5Key === code3;
  record('T5 неверный код -> 400', t5.status,
    `error_code=${t5Body.error_code || '?'} key_alive=${t5Key === code3}`, t5Pass);

  // T6: ключ удалён из Redis -> 410 (CAPTCHA_EXPIRED)
  log('\n=== T6: ключ удалён из Redis -> 410 ===');
  redisDel(c3.captcha_id);
  log(`  DEL "captcha:${c3.captcha_id.slice(0, 8)}…" -> redisGet="${redisGet(c3.captcha_id)}"`);
  const t6 = await api(`${MIN}/api/resources/mining/actions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JB({ captcha_id: c3.captcha_id, user_input: code3 }),
  });
  const t6Body = await t6.json().catch(() => ({}));
  log(`  T6 HTTP ${t6.status} | error_code=${t6Body.error_code}`);
  const t6Pass = t6.status === 410 && t6Body.error_code === 'CAPTCHA_EXPIRED';
  record('T6 ключ удалён -> 410', t6.status,
    `error_code=${t6Body.error_code || '?'}`, t6Pass);
  ok = results.every((r) => r.pass);
} catch (e) {
  log('\n❌ Фатальная ошибка: ' + (e && e.message ? e.message : String(e)));
  ok = false;
} finally {
  // возвращаем локацию персонажа в исходное состояние
  try {
    execSync(`docker exec character_service_db psql -U postgres -d character_service -c "UPDATE characters SET location_slug='${originalLocation}' WHERE id='${CHAR_ID}';"`, { encoding: 'utf8' });
    log(`\n=== TEARDOWN: location restored -> ${originalLocation} ===`);
  } catch (e) {
    log(`\n=== TEARDOWN: restore failed: ${(e && e.message ? e.message : String(e)).slice(0, 140)} ===`);
  }
}

log('\n==================== ИТОГ ====================');
log('| # | Сценарий | HTTP | Результат | Примечание |');
log('|---|----------|------|-----------|------------|');
for (const r of results) {
  const mark = r.pass ? '✅ PASS' : '❌ FAIL';
  const num = r.label.split(' ')[0];
  log(`| ${String(num).padEnd(2)} | ${r.label.padEnd(26)} | ${String(r.httpStatus).padEnd(4)} | ${mark.padEnd(8)} | ${r.detail} |`);
}
const passCount = results.filter((r) => r.pass).length;
const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
log(`\nИтого: ${passCount}/${results.length} passed`);
log(`Общее затраченное время: ${elapsed} с`);
log(ok
  ? '\n✅ B1-resources: паттерн подтвержден (409 до verify_captcha; капча сжигается только после успешного старта добычи).'
  : '\n❌ B1-resources: паттерн НЕ подтвержден.');
process.exit(ok ? 0 : 1);




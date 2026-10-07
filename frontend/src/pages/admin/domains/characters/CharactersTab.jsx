import { useState } from "react";
import {
  useSearchCharactersQuery,
  useGetCharacterQuery,
  useChangeDucatsMutation,
  useBanCharacterMutation,
  useUnbanCharacterMutation,
  useGetCharactersByUserQuery,
  useBanAllByUserMutation,
  useUnbanAllByUserMutation,
  useGetAuthLogsQuery,
  useGetTradePrivilegesQuery,
  useUpdateTradePrivilegesMutation,
} from "../../../../entities/admin/api";
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from "../../AdminPage.module.css";

/* ── хелперы уровня модуля ── */
function sortChars(chars, sortBy) {
  return [...chars].sort((a, b) => {
    if (sortBy === "level") return (b.level || 0) - (a.level || 0);
    if (sortBy === "name") return (a.name || "").localeCompare(b.name || "");
    return parseUtcDate(b.created_at) - parseUtcDate(a.created_at);
  });
}

function accountInfo(chars) {
  const created = chars.map((c) => parseUtcDate(c.created_at)).sort((a, b) => a - b)[0];
  const bannedCount = chars.filter((c) => c.is_banned).length;
  return { created, bannedCount };
}

const renderStatus = (char) => {
  if (char.is_banned) return <span className={styles.disabled}>Забанен</span>;
  if (char.is_active) return <span className={styles.enabled}>Активен</span>;
  return <span className={styles.neutral}>Откреплён</span>;
};

const renderName = (char) => (
  <>
    {char.name}
    {char.is_main && <span className={styles.mainBadge}> (Основа)</span>}
  </>
);

/* ── карточка аккаунта: сама тянет мультов и последний вход ── */
function AccountGroupCard({ userId, fallbackChars, sortBy, onSelect, notify }) {
  const { data: accountChars } = useGetCharactersByUserQuery(userId);
  const { data: logsResult } = useGetAuthLogsQuery({ user_id: userId, success: "true" });
  const [banAllByUser, banAllState] = useBanAllByUserMutation();
  const [unbanAllByUser, unbanAllState] = useUnbanAllByUserMutation();

  const chars = accountChars ?? fallbackChars;
  const lastLogin = logsResult?.objects?.[0]?.created_at || null;
  const info = accountInfo(chars);

  const handleBanAll = async () => {
    if (!confirm("Забанить ВСЕХ персонажей этого аккаунта?")) return;
    try {
      await banAllByUser(userId).unwrap();
      notify.success("Весь аккаунт забанен");
    } catch (e) {
      notify.error(e?.data?.detail || "Ошибка бана аккаунта");
    }
  };

  const handleUnbanAll = async () => {
    if (!confirm("Разбанить ВСЕХ персонажей этого аккаунта?")) return;
    try {
      await unbanAllByUser(userId).unwrap();
      notify.success("Весь аккаунт разбанен");
    } catch (e) {
      notify.error(e?.data?.detail || "Ошибка разбана аккаунта");
    }
  };

  return (
    <div className={styles.accountGroup}>
      <div className={styles.accountHeader}>
        <strong>Аккаунт:</strong> {userId.substring(0, 8)}...
        <span className={styles.accountCount}>
          {chars.length} перс. | Регистрация: {info.created?.toLocaleDateString() || "—"} |
          Забанено: {info.bannedCount}/{chars.length} |
          Последний вход: {lastLogin ? parseUtcDate(lastLogin).toLocaleString() : "—"}
        </span>
        <div className={styles.accountActions}>
          <button onClick={handleBanAll} disabled={banAllState.isLoading} className={styles.dangerBtn}>
            Забанить аккаунт
          </button>
          <button onClick={handleUnbanAll} disabled={unbanAllState.isLoading}>
            Разбанить аккаунт
          </button>
        </div>
      </div>
      <table className={styles.table}>
        <thead>
          <tr><th>Имя</th><th>Уровень</th><th>Статус</th><th>Действие</th></tr>
        </thead>
        <tbody>
          {sortChars(chars, sortBy).map((char) => (
            <tr key={char.id}>
              <td>{renderName(char)}</td>
              <td>{char.level}</td>
              <td>{renderStatus(char)}</td>
              <td><button onClick={() => onSelect(char.id)}>Выбрать</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── основной таб ── */
export default function CharactersTab() {
  const [filters, setFilters] = useState({
    name: "",
    character_id: "",
    user_id: "",
    is_active: "",
    is_online: ""
  });
  const [partialSearch, setPartialSearch] = useState(false);
  const [sortBy, setSortBy] = useState("created_at");
  const [loadTrigger, setLoadTrigger] = useState(false);
  const [selectedCharacterId, setSelectedCharacterId] = useState(null);
  const [ducatsAmount, setDucatsAmount] = useState("");
  const [ducatsReason, setDucatsReason] = useState("");
  const [banReason, setBanReason] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([_, v]) => v !== "")
  );
  const searchParams = { ...cleanFilters };
  if (searchParams.name && partialSearch) {
    searchParams.name_like = searchParams.name;
    delete searchParams.name;
  }

  const { data: searchResult, isLoading } = useSearchCharactersQuery(searchParams, { skip: !loadTrigger });
  const characters = searchResult?.objects || [];

  const { data: selectedCharacter } = useGetCharacterQuery(selectedCharacterId, { skip: !selectedCharacterId });

  const [changeDucatsMut, changeDucatsState] = useChangeDucatsMutation();
  const [banMut, banState] = useBanCharacterMutation();
  const [unbanMut, unbanState] = useUnbanCharacterMutation();
  const busy = changeDucatsState.isLoading || banState.isLoading || unbanState.isLoading;
  const { data: tradePrivileges } = useGetTradePrivilegesQuery(selectedCharacterId, { skip: !selectedCharacterId });
  const [privilegesMut, privilegesState] = useUpdateTradePrivilegesMutation();

  const notify = {
    success: (msg) => { setError(""); setSuccess(msg); },
    error: (msg) => { setSuccess(""); setError(msg); },
  };

  const uniqueUserIds = [...new Set(characters.map((c) => c.user_id).filter(Boolean))];

  const selectCharacter = (characterId) => {
    setSelectedCharacterId(characterId);
    setDucatsAmount("");
    setDucatsReason("");
    setBanReason("");
    setError("");
  };

  const handleChangeDucats = async () => {
    if (!selectedCharacter || !ducatsAmount) return;
    setError(""); setSuccess("");
    try {
      const result = await changeDucatsMut({
        characterId: selectedCharacter.id,
        amount: parseFloat(ducatsAmount),
        reason: ducatsReason || null,
      }).unwrap();
      setSuccess(`Дукаты изменены. Новый баланс: ${result.balance_after}`);
    } catch (e) {
      setError(e?.data?.detail || "Ошибка изменения дукатов");
    }
  };

  const handleTogglePrivileges = async () => {
    if (!selectedCharacter || !tradePrivileges) return;
    setError(""); setSuccess("");
    try {
      await privilegesMut({
        characterId: selectedCharacter.id,
        enabled: !tradePrivileges.gold_trade_enabled,
      }).unwrap();
      notify.success("Права обновлены");
    } catch (e) {
      notify.error(e?.data?.detail || "Ошибка обновления");
    }
  };

  const handleBanCharacter = async () => {
    if (!selectedCharacter) return;
    setError(""); setSuccess("");
    try {
      await banMut({ characterId: selectedCharacter.id, reason: banReason || null }).unwrap();
      setSuccess("Персонаж забанен");
    } catch (e) {
      setError(e?.data?.detail || "Ошибка бана");
    }
  };

  const handleUnbanCharacter = async () => {
    if (!selectedCharacter) return;
    setError(""); setSuccess("");
    try {
      await unbanMut(selectedCharacter.id).unwrap();
      setSuccess("Персонаж разбанен");
    } catch (e) {
      setError(e?.data?.detail || "Ошибка разбана");
    }
  };

  return (
    <div>
      {/* Фильтры */}
      <div className={styles.filters}>
        <input
          type="text"
          placeholder="Имя персонажа"
          value={filters.name}
          onChange={(e) => setFilters({ ...filters, name: e.target.value })}
        />
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={partialSearch}
            onChange={(e) => setPartialSearch(e.target.checked)}
          />
          Частичный поиск
        </label>
        <input
          type="text"
          placeholder="Character ID"
          value={filters.character_id}
          onChange={(e) => setFilters({ ...filters, character_id: e.target.value })}
        />
        <input
          type="text"
          placeholder="User ID"
          value={filters.user_id}
          onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
        />
        <select
          value={filters.is_active}
          onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
        >
          <option value="">Все статусы</option>
          <option value="true">Активные</option>
          <option value="false">Забаненные</option>
        </select>
        <select
          value={filters.is_online}
          onChange={(e) => setFilters({ ...filters, is_online: e.target.value })}
        >
          <option value="">Все</option>
          <option value="true">Онлайн</option>
          <option value="false">Оффлайн</option>
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="created_at">По дате создания</option>
          <option value="level">По уровню</option>
          <option value="name">По имени</option>
        </select>
        <button onClick={() => setLoadTrigger(true)} disabled={isLoading}>
          Найти
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.charactersGrid}>
        {/* Список результатов */}
        <div className={styles.charactersList}>
          <h3>Результаты ({characters.length})</h3>

          {uniqueUserIds.length > 0 ? (
            uniqueUserIds.map((userId) => (
              <AccountGroupCard
                key={userId}
                userId={userId}
                fallbackChars={characters.filter((c) => c.user_id === userId)}
                sortBy={sortBy}
                onSelect={selectCharacter}
                notify={notify}
              />
            ))
          ) : (
            <table className={styles.table}>
              <thead>
                <tr><th>Имя</th><th>Уровень</th><th>Статус</th><th>Действие</th></tr>
              </thead>
              <tbody>
                {sortChars(characters, sortBy).map((char) => (
                  <tr key={char.id}>
                    <td>{renderName(char)}</td>
                    <td>{char.level}</td>
                    <td>{renderStatus(char)}</td>
                    <td><button onClick={() => selectCharacter(char.id)}>Выбрать</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Детальная карточка */}
        {selectedCharacter && (
          <div className={styles.characterDetails}>
            <h3>Детали персонажа</h3>
            <div className={styles.detailRow}><strong>Имя:</strong> {renderName(selectedCharacter)}</div>
            <div className={styles.detailRow}><strong>ID:</strong> {selectedCharacter.id}</div>
            <div className={styles.detailRow}>
              <strong>User ID:</strong>{" "}
              <code className={styles.code}>{selectedCharacter.user_id}</code>
            </div>
            <div className={styles.detailRow}><strong>Уровень:</strong> {selectedCharacter.level}</div>
            <div className={styles.detailRow}><strong>Дукаты:</strong> {selectedCharacter.ducats}</div>
            <div className={styles.detailRow}><strong>Золото:</strong> {selectedCharacter.gold}</div>
            <div className={styles.detailRow}><strong>Статус:</strong> {renderStatus(selectedCharacter)}</div>
            <div className={styles.detailRow}><strong>Онлайн:</strong> {selectedCharacter.is_online ? "Да" : "Нет"}</div>

            <h4>Изменить дукаты</h4>
            <input
              type="number"
              placeholder="Сумма (+/-)"
              value={ducatsAmount}
              onChange={(e) => setDucatsAmount(e.target.value)}
            />
            <input
              type="text"
              placeholder="Причина"
              value={ducatsReason}
              onChange={(e) => setDucatsReason(e.target.value)}
            />
            <button onClick={handleChangeDucats} disabled={busy || !ducatsAmount}>
              Изменить дукаты
            </button>

            <h4>Торговые права</h4>
            <div className={styles.detailRow}>
              <strong>Торговля золотом:</strong>{" "}
              {tradePrivileges ? (
                <span className={tradePrivileges.gold_trade_enabled ? styles.enabled : styles.disabled}>
                  {tradePrivileges.gold_trade_enabled ? "Включена" : "Отключена"}
                </span>
              ) : (
                "—"
              )}
            </div>
            <button
              onClick={handleTogglePrivileges}
              disabled={privilegesState.isLoading || !tradePrivileges}
            >
              {tradePrivileges?.gold_trade_enabled ? "Отключить торговлю золотом" : "Включить торговлю золотом"}
            </button>

            <h4>Управление баном (персонаж)</h4>
            <input
              type="text"
              placeholder="Причина бана"
              value={banReason}
              onChange={(e) => setBanReason(e.target.value)}
            />
            {selectedCharacter.is_banned ? (
              <button onClick={handleUnbanCharacter} disabled={busy}>Разбанить</button>
            ) : (
              <button onClick={handleBanCharacter} disabled={busy}>Забанить</button>
            )}

            <h4>Управление баном (аккаунт)</h4>
            <div className={styles.accountActions}>              
              <AccountBanButtons userId={selectedCharacter.user_id} notify={notify} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── кнопки бана аккаунта в детальной карточке ── */
function AccountBanButtons({ userId, notify }) {
  const [banAllByUser, banAllState] = useBanAllByUserMutation();
  const [unbanAllByUser, unbanAllState] = useUnbanAllByUserMutation();

  const handleBanAll = async () => {
    if (!confirm("Забанить ВСЕХ персонажей этого аккаунта?")) return;
    try {
      await banAllByUser(userId).unwrap();
      notify.success("Весь аккаунт забанен");
    } catch (e) {
      notify.error(e?.data?.detail || "Ошибка бана аккаунта");
    }
  };

  const handleUnbanAll = async () => {
    if (!confirm("Разбанить ВСЕХ персонажей этого аккаунта?")) return;
    try {
      await unbanAllByUser(userId).unwrap();
      notify.success("Весь аккаунт разбанен");
    } catch (e) {
      notify.error(e?.data?.detail || "Ошибка разбана аккаунта");
    }
  };

  return (
    <>
      <button onClick={handleBanAll} disabled={banAllState.isLoading} className={styles.dangerBtn}>
        Забанить весь аккаунт
      </button>
      <button onClick={handleUnbanAll} disabled={unbanAllState.isLoading}>
        Разбанить аккаунт
      </button>
    </>
  );
}
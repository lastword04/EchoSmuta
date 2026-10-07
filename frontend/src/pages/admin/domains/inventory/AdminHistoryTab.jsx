import { useEffect, useState } from "react";
import {
  useListAdminCharactersQuery,
  useGetAdminLogsQuery,
} from "../../../../entities/admin/api";
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from "../../AdminPage.module.css";

const ACTION_LABELS = {
  give_item: "Выдан предмет",
  take_item: "Забран предмет",
  give_resource: "Выдан ресурс",
  take_resource: "Забран ресурс",
  money_add: "Добавлены деньги",
  money_set: "Установлены деньги",
};

export default function AdminHistoryTab() {
  const [characterId, setCharacterId] = useState("");
  const [characterSearch, setCharacterSearch] = useState("");
  const [searchTrigger, setSearchTrigger] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const { data: searchResult } = useListAdminCharactersQuery(
    { search: searchTrigger, limit: 10 },
    { skip: !searchTrigger }
  );
  const characterResults = searchResult?.objects || [];

  const { data: logsResult, isLoading, error } = useGetAdminLogsQuery(
    { character_id: characterId || undefined, limit, offset },
    { skip: !characterId }
  );
  const logs = logsResult?.objects || [];
  const count = logsResult?.count || 0;

  useEffect(() => {
    const search = characterSearch.trim();
    if (!search) {
      setSearchTrigger("");
      return;
    }
    const timer = setTimeout(() => setSearchTrigger(search), 300);
    return () => clearTimeout(timer);
  }, [characterSearch]);

  const loadLogs = (nextOffset) => setOffset(nextOffset);

  return (
    <div>
      <div className={styles.filters}>
        <div className={styles.historyCharacterSearch}>
          <input
            placeholder="Введите имя персонажа"
            value={characterSearch}
            onChange={(e) => {
              setCharacterSearch(e.target.value);
              setCharacterId("");
            }}
          />
          {characterResults.length > 0 && !characterId && (
            <div className={styles.historyCharacterDropdown}>
              {characterResults.map((character) => (
                <button
                  type="button"
                  key={character.id}
                  onClick={() => {
                    setCharacterId(character.id);
                    setCharacterSearch(character.name);
                    setSearchTrigger("");
                  }}
                >
                  {character.name} <span>{character.id}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        {characterId && <code className={styles.code}>{characterId}</code>}
        <button onClick={() => loadLogs(0)} disabled={isLoading || !characterId}>Загрузить</button>
      </div>
      {error && <div className={styles.error}>{error?.data?.detail || "Ошибка загрузки истории"}</div>}
      <table className={styles.table}>
        <thead><tr><th>Дата</th><th>Администратор</th><th>Персонаж</th><th>Действие</th><th>Детали</th></tr></thead>
        <tbody>{logs.map((log) => <tr key={log.id}><td>{parseUtcDate(log.created_at).toLocaleString()}</td><td><code className={styles.code}>{log.admin_user_id}</code></td><td><code className={styles.code}>{log.character_id}</code></td><td>{ACTION_LABELS[log.action] || log.action}</td><td><pre className={styles.logDetails}>{JSON.stringify(log.details, null, 2)}</pre></td></tr>)}</tbody>
      </table>
      {!isLoading && logs.length === 0 && <div className={styles.empty}>Нет записей</div>}
      <div className={styles.pagination}>
        <button onClick={() => loadLogs(Math.max(0, offset - limit))} disabled={isLoading || offset === 0}>Назад</button>
        <span>{count ? `${offset + 1}–${Math.min(offset + limit, count)} из ${count}` : "0 записей"}</span>
        <button onClick={() => loadLogs(offset + limit)} disabled={isLoading || offset + limit >= count}>Вперёд</button>
      </div>
    </div>
  );
}
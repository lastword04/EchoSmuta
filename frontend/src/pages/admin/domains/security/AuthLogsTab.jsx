import { useState } from "react";
import { useGetAuthLogsQuery } from "../../../../entities/admin/api";
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from "../../AdminPage.module.css";

export default function AuthLogsTab() {
  const [filters, setFilters] = useState({
    character_name: "",
    user_id: "",
    success: ""
  });
  const [loadTrigger, setLoadTrigger] = useState(false);

  const { data: logsResult, isLoading, error } = useGetAuthLogsQuery(
    Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== "")),
    { skip: !loadTrigger }
  );
  const allLogs = logsResult?.objects || [];

  const groupedByUser = {};
  const unknownLogs = [];
  allLogs.forEach((log) => {
    if (log.user_id) {
      if (!groupedByUser[log.user_id]) groupedByUser[log.user_id] = [];
      groupedByUser[log.user_id].push(log);
    } else {
      unknownLogs.push(log);
    }
  });

  const accountInfo = (accountLogs) => {
    const names = [...new Set(accountLogs.map((l) => l.character_name))];
    const successful = accountLogs.filter((l) => l.success);
    const lastLogin =
      successful.length > 0
        ? parseUtcDate(Math.max(...successful.map((l) => parseUtcDate(l.created_at))))
        : null;
    return { names, lastLogin };
  };

  const renderLogTable = (accountLogs) => (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Персонаж</th>
          <th>IP</th>
          <th>Статус</th>
          <th>Причина ошибки</th>
          <th>User Agent</th>
          <th>Дата</th>
        </tr>
      </thead>
      <tbody>
        {accountLogs.map((log) => (
          <tr key={log.id}>
            <td>{log.character_name}</td>
            <td>{log.ip_address}</td>
            <td>
              <span className={log.success ? styles.enabled : styles.disabled}>
                {log.success ? "Успех" : "Неудача"}
              </span>
            </td>
            <td>{log.error_reason || "-"}</td>
            <td>{log.user_agent ? log.user_agent.substring(0, 50) + "..." : "-"}</td>
            <td>{parseUtcDate(log.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div>
      <div className={styles.filters}>
        <input
          type="text"
          placeholder="Имя персонажа"
          value={filters.character_name}
          onChange={(e) => setFilters({ ...filters, character_name: e.target.value })}
        />
        <input
          type="text"
          placeholder="User ID"
          value={filters.user_id}
          onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
        />
        <select
          value={filters.success}
          onChange={(e) => setFilters({ ...filters, success: e.target.value })}
        >
          <option value="">Все попытки</option>
          <option value="true">Успешные</option>
          <option value="false">Неудачные</option>
        </select>
        <button onClick={() => setLoadTrigger(true)} disabled={isLoading}>
          Загрузить
        </button>
      </div>

      {error && <div className={styles.error}>{error?.data?.detail || "Ошибка загрузки"}</div>}

      {Object.entries(groupedByUser).map(([userId, accountLogs]) => {
        const info = accountInfo(accountLogs);
        return (
          <div key={userId} className={styles.accountGroup}>
            <div className={styles.accountHeader}>
              <strong>Аккаунт:</strong> {userId.substring(0, 8)}...
              <span className={styles.accountCount}>
                {accountLogs.length} записей | Персонажи: {info.names.join(", ")} |
                Последний вход: {info.lastLogin ? info.lastLogin.toLocaleString() : "—"}
              </span>
            </div>
            {renderLogTable(accountLogs)}
          </div>
        );
      })}

      {unknownLogs.length > 0 && (
        <div className={styles.accountGroup}>
          <div className={styles.accountHeader}>
            <strong>Неопознанные входы</strong>
            <span className={styles.accountCount}>{unknownLogs.length} записей</span>
          </div>
          {renderLogTable(unknownLogs)}
        </div>
      )}

      {allLogs.length === 0 && !isLoading && (
        <div className={styles.empty}>Нет логов</div>
      )}
    </div>
  );
}
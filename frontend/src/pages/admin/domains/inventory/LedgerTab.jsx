import { useState } from "react";
import {
  useGetCurrencyOperationsQuery,
  useGetCompletingDealsQuery,
} from "../../../../entities/admin/api";
import CharacterPicker from "../../shared/CharacterPicker";
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from "../../AdminPage.module.css";

export default function LedgerTab() {
  const [filters, setFilters] = useState({
    character_id: "",
    currency: "",
    operation_type: "",
    source: ""
  });
  const [loadTrigger, setLoadTrigger] = useState(false);

  const [showDeals, setShowDeals] = useState(false);
  const [dealsTrigger, setDealsTrigger] = useState(false);

  const { data: operationsResult, isLoading, error } = useGetCurrencyOperationsQuery(
    filters,
    { skip: !loadTrigger }
  );
  const operations = operationsResult?.objects || [];

  const { data: dealsResult, isLoading: dealsLoading } = useGetCompletingDealsQuery(50, { skip: !dealsTrigger });
  const deals = dealsResult?.objects || [];

  const toggleDeals = () => {
    const next = !showDeals;
    setShowDeals(next);
    if (next && !dealsTrigger) setDealsTrigger(true);
  };

  return (
    <div>
      {/* Заголовок + сделки рядышком */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Валютные операции</h3>
        <button onClick={toggleDeals} disabled={dealsLoading}>
          {showDeals ? "Скрыть зависшие сделки" : `Зависшие сделки${deals.length ? ` (${deals.length})` : ""}`}
        </button>
      </div>

      {showDeals && (
        <div style={{ marginBottom: 20 }}>
          {deals.length === 0 ? (
            <div className={styles.empty}>Нет зависших сделок</div>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr><th>Deal ID</th><th>Initiator</th><th>Partner</th><th>Статус</th><th>Создана</th></tr>
              </thead>
              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id}>
                    <td>{deal.id.substring(0, 8)}...</td>
                    <td>{deal.initiator_character_id.substring(0, 8)}...</td>
                    <td>{deal.partner_character_id.substring(0, 8)}...</td>
                    <td>{deal.status}</td>
                    <td>{parseUtcDate(deal.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className={styles.filters}>
        <CharacterPicker
          onSelect={(id) => setFilters({ ...filters, character_id: id })}
        />
        {filters.character_id && (
          <button
            type="button"
            onClick={() => setFilters({ ...filters, character_id: "" })}
          >
            ✕ {filters.character_id.substring(0, 8)}...
          </button>
        )}
        <select
          value={filters.currency}
          onChange={(e) => setFilters({ ...filters, currency: e.target.value })}
        >
          <option value="">Все валюты</option>
          <option value="ducats">Дукаты</option>
          <option value="gold">Золото</option>
        </select>
        <input
          type="text"
          placeholder="Operation type"
          value={filters.operation_type}
          onChange={(e) => setFilters({ ...filters, operation_type: e.target.value })}
        />
        <input
          type="text"
          placeholder="Source"
          value={filters.source}
          onChange={(e) => setFilters({ ...filters, source: e.target.value })}
        />
        <button onClick={() => setLoadTrigger(true)} disabled={isLoading}>
          Загрузить
        </button>
      </div>

      {error && <div className={styles.error}>{error?.data?.detail || "Ошибка загрузки"}</div>}

      <table className={styles.table}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Character ID</th>
            <th>Валюта</th>
            <th>Тип</th>
            <th>Сумма</th>
            <th>Баланс после</th>
            <th>Источник</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {operations.map((op) => (
            <tr key={op.id}>
              <td>{op.id.substring(0, 8)}...</td>
              <td>{op.character_id.substring(0, 8)}...</td>
              <td>{op.currency}</td>
              <td>{op.operation_type}</td>
              <td>{op.amount}</td>
              <td>{op.balance_after}</td>
              <td>{op.source}</td>
              <td>{parseUtcDate(op.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
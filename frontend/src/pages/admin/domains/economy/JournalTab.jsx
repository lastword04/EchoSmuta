import { useState } from 'react';
import {
  useGetTransactionsQuery,
  useGetResourcesQuery,
} from '../../../../entities/admin/api';
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';

const TRANSACTION_TYPES = [
  { value: 'BUYOUT_BUY', label: '🛒 Скупка: покупка' },
  { value: 'BUYOUT_SELL', label: '💰 Скупка: продажа' },
  { value: 'EXCHANGE_BUY', label: '🔄 Сделки: покупка' },
  { value: 'EXCHANGE_SELL', label: '🔄 Сделки: продажа' },
  { value: 'EXCHANGE_CANCEL', label: '❌ Сделки: отмена' },
  { value: 'ADMIN_RESET', label: '⚙️ Админ: сброс' },
];

export default function JournalTab() {
  const [filters, setFilters] = useState({
    transaction_type: '',
    resource_id: '',
    start_date: '',
    end_date: '',
    limit: 50,
    offset: 0,
  });

  // RTK Query автоматически делает запрос при изменении filters
  const { data: transactions = [], isLoading: isTxLoading, error: txError } = useGetTransactionsQuery(filters);
  const { data: resources = [] } = useGetResourcesQuery();

  const isLoading = isTxLoading;
  const error = txError;

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value, offset: 0 })); // Сброс на 1-ю страницу
  };

  const handlePrevPage = () => {
    setFilters((prev) => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }));
  };

  const handleNextPage = () => {
    setFilters((prev) => ({ ...prev, offset: prev.offset + prev.limit }));
  };

  const clearFilters = () => {
    setFilters({ transaction_type: '', resource_id: '', start_date: '', end_date: '', limit: 50, offset: 0 });
  };

  const getResourceName = (resourceId) => {
    const r = resources.find((res) => res.id === resourceId);
    return r ? r.name : (resourceId ? String(resourceId) : '—');
  };

  if (isLoading) return <div style={{ padding: 20 }}>Загрузка...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>Ошибка: {error.message || 'Не удалось загрузить'}</div>;

  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const isNextDisabled = transactions.length < filters.limit;

  return (
    <div style={{ padding: 20, fontSize: 14 }}>
      <div style={{ marginBottom: 20, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', background: '#f9f9f9', padding: 16, borderRadius: 8 }}>
        <select value={filters.transaction_type} onChange={(e) => handleFilterChange('transaction_type', e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }}>
          <option value="">Все типы операций</option>
          {TRANSACTION_TYPES.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
        </select>

        <select value={filters.resource_id} onChange={(e) => handleFilterChange('resource_id', e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc', minWidth: 180 }}>
          <option value="">Все ресурсы</option>
          {resources.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
        </select>

        <input type="date" value={filters.start_date} onChange={(e) => handleFilterChange('start_date', e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }} title="Дата с" />
        <span style={{ color: '#666' }}>—</span>
        <input type="date" value={filters.end_date} onChange={(e) => handleFilterChange('end_date', e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }} title="Дата по" />

        <button onClick={clearFilters} style={{ padding: '8px 16px', fontSize: 14, background: '#dc3545', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', marginLeft: 'auto' }}>
          Сбросить всё
        </button>
      </div>

      <div style={{ marginBottom: 10, color: '#666', fontSize: 13 }}>
        Показано на странице: {transactions.length}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
            <th style={{ padding: 10, textAlign: 'left' }}>Ресурс</th>
            <th style={{ padding: 10, textAlign: 'right' }}>Кол-во</th>
            <th style={{ padding: 10, textAlign: 'right' }}>Цена/ед</th>
            <th style={{ padding: 10, textAlign: 'right' }}>Сумма</th>
            <th style={{ padding: 10, textAlign: 'left' }}>Покупатель (ID)</th>
            <th style={{ padding: 10, textAlign: 'left' }}>Продавец (ID)</th>
            <th style={{ padding: 10, textAlign: 'left' }}>Дата</th>
          </tr>
        </thead>
        <tbody>
          {transactions.length === 0 ? (
            <tr><td colSpan={7} style={{ padding: 30, textAlign: 'center', color: '#888' }}>Транзакции не найдены</td></tr>
          ) : (
            transactions.map((tx) => (
              <tr key={tx.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 10 }}>{getResourceName(tx.resource_id)}</td>
                <td style={{ padding: 10, textAlign: 'right' }}>{tx.quantity}</td>
                <td style={{ padding: 10, textAlign: 'right' }}>{Number(tx.price_per_unit).toFixed(2)}</td>
                <td style={{ padding: 10, textAlign: 'right', fontWeight: 600 }}>{Number(tx.total).toFixed(2)}</td>
                <td style={{ padding: 10, fontSize: 11, fontFamily: 'monospace', color: '#555' }}>{tx.buyer_id || '—'}</td>
                <td style={{ padding: 10, fontSize: 11, fontFamily: 'monospace', color: '#555' }}>{tx.seller_id || '—'}</td>
                <td style={{ padding: 10, fontSize: 12, whiteSpace: 'nowrap' }}>{parseUtcDate(tx.created_at).toLocaleString('ru-RU')}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: 12 }}>
        <button onClick={handlePrevPage} disabled={filters.offset === 0} style={{ padding: '8px 16px', fontSize: 14, background: filters.offset === 0 ? '#ccc' : '#007bff', color: 'white', border: 'none', borderRadius: 4, cursor: filters.offset === 0 ? 'not-allowed' : 'pointer' }}>
          ← Назад
        </button>
        <span style={{ padding: '8px 16px', fontSize: 14, alignSelf: 'center' }}>Страница {currentPage}</span>
        <button onClick={handleNextPage} disabled={isNextDisabled} style={{ padding: '8px 16px', fontSize: 14, background: isNextDisabled ? '#ccc' : '#007bff', color: 'white', border: 'none', borderRadius: 4, cursor: isNextDisabled ? 'not-allowed' : 'pointer' }}>
          Вперёд →
        </button>
      </div>
    </div>
  );
}
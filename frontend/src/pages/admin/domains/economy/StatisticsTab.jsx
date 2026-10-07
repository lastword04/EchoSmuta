import { useState } from 'react';
import { useGetStatisticsQuery } from '../../../../entities/admin/api';

export default function StatisticsTab() {
  const today = new Date().toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(today);
  
  // RTK Query автоматически перезапрашивает данные при изменении startDate или endDate
  const { data: stats, isLoading, error } = useGetStatisticsQuery({ startDate, endDate });

  const TYPE_LABELS = {
    'BUYOUT_BUY': '🛒 Скупка: покупка',
    'BUYOUT_SELL': '💰 Скупка: продажа',
    'EXCHANGE_BUY': '🔄 Сделки: покупка',
    'EXCHANGE_SELL': '🔄 Сделки: продажа',
    'EXCHANGE_CANCEL': '❌ Сделки: отмена',
    'ADMIN_RESET': '⚙️ Админ: сброс',
  };

  if (isLoading) return <div style={{ padding: 20 }}>Загрузка...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>Ошибка: {error.message || 'Не удалось загрузить'}</div>;

  return (
    <div style={{ padding: 20, fontSize: 14 }}>
      <div style={{ marginBottom: 24, display: 'flex', gap: 16, alignItems: 'center', background: '#f9f9f9', padding: 16, borderRadius: 8 }}>
        <span style={{ fontWeight: 600 }}>Период:</span>
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }} />
        <span>—</span>
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={{ padding: '8px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }} />
      </div>

      {stats && (
        <>
          <div style={{ display: 'flex', gap: 20, marginBottom: 24 }}>
            <div style={{ flex: 1, background: '#e3f2fd', padding: 20, borderRadius: 8, border: '1px solid #bbdefb' }}>
              <div style={{ fontSize: 12, color: '#555', marginBottom: 8 }}>Всего транзакций</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#1976d2' }}>{stats.total_transactions}</div>
            </div>
            <div style={{ flex: 1, background: '#e8f5e9', padding: 20, borderRadius: 8, border: '1px solid #c8e6c9' }}>
              <div style={{ fontSize: 12, color: '#555', marginBottom: 8 }}>Общий оборот (дукаты)</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#388e3c' }}>{stats.total_volume.toLocaleString('ru-RU', { maximumFractionDigits: 2 })}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 20 }}>
            <div style={{ flex: 1, background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 20 }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: 16 }}>🏆 Топ-5 ресурсов по обороту</h3>
              {stats.top_resources.length === 0 ? (
                <div style={{ color: '#888' }}>Нет данных за период</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                      <th style={{ padding: 8 }}>Ресурс</th>
                      <th style={{ padding: 8, textAlign: 'right' }}>Оборот</th>
                      <th style={{ padding: 8, textAlign: 'right' }}>Сделок</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_resources.map((r, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #f5f5f5' }}>
                        <td style={{ padding: 10, fontWeight: 500 }}>{r.name}</td>
                        <td style={{ padding: 10, textAlign: 'right', color: '#388e3c', fontWeight: 600 }}>{r.volume.toLocaleString('ru-RU', { maximumFractionDigits: 2 })}</td>
                        <td style={{ padding: 10, textAlign: 'right', color: '#666' }}>{r.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div style={{ flex: 1, background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 20 }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: 16 }}>📊 Распределение по типам</h3>
              {Object.keys(stats.by_type).length === 0 ? (
                <div style={{ color: '#888' }}>Нет данных за период</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <tbody>
                    {Object.entries(stats.by_type).map(([type, count]) => (
                      <tr key={type} style={{ borderBottom: '1px solid #f5f5f5' }}>
                        <td style={{ padding: 10 }}>{TYPE_LABELS[type] || type}</td>
                        <td style={{ padding: 10, textAlign: 'right', fontWeight: 600 }}>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
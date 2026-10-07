import { useEffect, useState } from 'react';
import {
  useGetResourcesQuery,
  useSetStockMutation,
  useSetPricesMutation,
  useRecalculatePricesMutation,
} from '../../../../entities/admin/api';
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';

const CATEGORIES = [
  { key: 'swamp', label: '🌿 Болото' },
  { key: 'mine', label: '⛏️ Шахта' },
  { key: 'gems', label: '💎 Самоцветы' },
  { key: 'lake', label: '🌊 Озеро' },
  { key: 'forest', label: '🌲 Лес' },
  { key: 'sands', label: '🏜️ Пески' },
  { key: 'skins', label: '🐾 Шкуры' },
];

export default function EconomyTab() {
  const [activeCategory, setActiveCategory] = useState('swamp');
  const [drafts, setDrafts] = useState({});
  const [saving, setSaving] = useState({});

  // RTK Query хуки заменяют ручные useState для loading/error/data
  const { data: resources = [], isLoading, error } = useGetResourcesQuery();
  const [setStock] = useSetStockMutation();
  const [setPrices] = useSetPricesMutation();
  const [recalculatePrices, { isLoading: isRecalculating }] = useRecalculatePricesMutation();

  // Инициализируем черновики при загрузке ресурсов
  useEffect(() => {
    if (resources.length > 0) {
      const initialDrafts = {};
      resources.forEach((r) => {
        initialDrafts[r.id] = {
          quantity: r.stock_quantity ?? 0,
          baseSellPrice: r.base_sell_price ?? '',
          baseBuyPrice: r.base_buy_price ?? '',
          sellPrice: r.sell_price ?? '',
          buyPrice: r.buy_price ?? '',
        };
      });
      setDrafts(initialDrafts);
    }
  }, [resources]);

  const updateDraft = (id, patch) => {
    setDrafts((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  };

  const saveResource = async (resourceId) => {
    const d = drafts[resourceId];
    setSaving((prev) => ({ ...prev, [resourceId]: true }));
    try {
      const stockBody = { quantity: Number(d.quantity) };
      if (d.baseSellPrice !== '') stockBody.base_sell_price = Number(d.baseSellPrice);
      if (d.baseBuyPrice !== '') stockBody.base_buy_price = Number(d.baseBuyPrice);
      
      // unwrap() пробрасывает ошибку в catch, если запрос не удался
      await setStock({ resourceId, body: stockBody }).unwrap();

      const priceBody = {};
      if (d.sellPrice !== '') priceBody.sell_price = Number(d.sellPrice);
      if (d.buyPrice !== '') priceBody.buy_price = Number(d.buyPrice);
      
      await setPrices({ resourceId, body: priceBody }).unwrap();
    } catch (e) {
      alert('Ошибка сохранения: ' + (e?.data?.detail || e?.message || 'unknown'));
    } finally {
      setSaving((prev) => ({ ...prev, [resourceId]: false }));
    }
  };

  const handleRecalculate = async () => {
    try {
      await recalculatePrices(true).unwrap();
    } catch (e) {
      alert('Ошибка пересчёта: ' + (e?.data?.detail || e?.message || 'unknown'));
    }
  };

  const filteredResources = resources.filter((r) => {
    const categoryMap = {
      swamp: 'swamp', mine: 'mine', gems: 'gems', lake: 'lake',
      forest: 'forest', sands: 'sands', skins: 'skins',
    };
    return categoryMap[r.category] === activeCategory;
  });

  // Находим ближайшую дату пересчета из полученных ресурсов
  const nextRecalcAt = resources.reduce((earliest, r) => {
    if (!r.next_recalculation_at) return earliest;
    const d = parseUtcDate(r.next_recalculation_at);
    return !earliest || d < earliest ? d : earliest;
  }, null);

  if (isLoading) return <div style={{ padding: 20 }}>Загрузка...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>Ошибка: {error.message || 'Не удалось загрузить'}</div>;

  return (
    <div style={{ padding: 20, fontSize: 14 }}>
      <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={handleRecalculate} disabled={isRecalculating} style={{ padding: '8px 16px', fontSize: 14 }}>
          {isRecalculating ? 'Пересчёт...' : '🔄 Пересчитать цены'}
        </button>
        {nextRecalcAt && (
          <span style={{ fontSize: 13, color: '#666' }}>
            Следующий пересчёт: {nextRecalcAt.toLocaleString('ru-RU')}
          </span>
        )}
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            style={{
              padding: '8px 16px', fontSize: 14,
              background: activeCategory === cat.key ? '#007bff' : '#f0f0f0',
              color: activeCategory === cat.key ? 'white' : 'black',
              border: 'none', borderRadius: 4, cursor: 'pointer',
            }}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
            <th style={{ padding: 12, textAlign: 'left' }}>Ресурс</th>
            <th style={{ padding: 12, textAlign: 'center' }}>📦 Сток</th>
            <th colSpan={2} style={{ padding: 12, textAlign: 'center', borderBottom: '2px solid #ccc' }}>💰 Текущие цены</th>
            <th colSpan={2} style={{ padding: 12, textAlign: 'center', borderBottom: '2px solid #ccc' }}>📍 Базовые цены</th>
            <th style={{ padding: 12 }}></th>
          </tr>
          <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
            <th></th><th></th>
            <th style={{ padding: 8 }}>Sell</th><th style={{ padding: 8 }}>Buy</th>
            <th style={{ padding: 8 }}>Sell</th><th style={{ padding: 8 }}>Buy</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {filteredResources.map((r) => {
            const d = drafts[r.id] || {};
            const isSaving = saving[r.id] || false;
            return (
              <tr key={r.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 12 }}>
                  <div style={{ fontWeight: 600 }}>{r.name}</div>
                  <div style={{ fontSize: 11, color: '#888', fontFamily: 'monospace' }}>{r.code}</div>
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <input type="number" value={d.quantity ?? ''} onChange={(e) => updateDraft(r.id, { quantity: e.target.value })} style={{ width: 80, padding: 6, fontSize: 14 }} />
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <input type="number" step="0.01" value={d.sellPrice ?? ''} onChange={(e) => updateDraft(r.id, { sellPrice: e.target.value })} style={{ width: 80, padding: 6, fontSize: 14 }} />
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <input type="number" step="0.01" value={d.buyPrice ?? ''} onChange={(e) => updateDraft(r.id, { buyPrice: e.target.value })} style={{ width: 80, padding: 6, fontSize: 14 }} />
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <input type="number" step="0.01" value={d.baseSellPrice ?? ''} onChange={(e) => updateDraft(r.id, { baseSellPrice: e.target.value })} style={{ width: 80, padding: 6, fontSize: 14 }} />
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <input type="number" step="0.01" value={d.baseBuyPrice ?? ''} onChange={(e) => updateDraft(r.id, { baseBuyPrice: e.target.value })} style={{ width: 80, padding: 6, fontSize: 14 }} />
                </td>
                <td style={{ padding: 12, textAlign: 'center' }}>
                  <button onClick={() => saveResource(r.id)} disabled={isSaving} style={{ padding: '6px 16px', fontSize: 14, background: isSaving ? '#ccc' : '#28a745', color: 'white', border: 'none', borderRadius: 4, cursor: isSaving ? 'not-allowed' : 'pointer' }}>
                    {isSaving ? '...' : '💾 Сохранить'}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
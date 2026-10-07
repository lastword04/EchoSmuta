import { useMemo, useRef } from "react";
import { useGetSalesHistoryQuery } from "../../../entities/items/api/inventoryApi"; 
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from "./SalesHistoryView.module.css";
import { DataState } from '../../../shared/ui/DataState/DataState';

const pad = (n) => String(n).padStart(2, "0");

const formatDate = (iso) => {
  if (!iso) return "—";
  const d = parseUtcDate(iso);
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

function SalesHistoryView({ locationSlug }) {  
  const lastDataRef = useRef(null);

  // ═══ RTK QUERY ═══
  const { 
    data, 
    error, 
    isLoading, 
    refetch 
  } = useGetSalesHistoryQuery(
    { limit: 30, locationSlug },
    { 
      skip: !locationSlug,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (data !== undefined && data !== null) {
    lastDataRef.current = data;
  }
  const displayData = data !== undefined ? data : lastDataRef.current;
 

  // ═══ COMPUTED ═══
  const sales = useMemo(() => {
    if (!displayData) return [];
    return Array.isArray(displayData) ? displayData : (displayData?.items || []);
  }, [displayData]);

  // ═══ RENDER ═══
  if (!displayData && isLoading) return null;

  return (
    <div className={styles.historyContainer}>
      <DataState
        error={!!error}
        errorMessage="Не удалось загрузить историю продаж"
        onRetry={refetch}
        isEmpty={sales.length === 0}
        emptyMessage="Продаж пока нет"
        isLoading={isLoading}
      >
        <div className={styles.borderBox}>
          <table className={styles.historyTable}>
            <colgroup>
              <col /><col /><col /><col /><col />
            </colgroup>
            <thead>
              <tr>
                <th className={styles.hideOnMobile}>Дата</th>
                <th>Товар</th>
                <th>Цена</th>
                <th className={styles.hideOnMobile}>Налог</th>
                <th>Покупатель</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((row) => (
                <tr key={row.id}>
                  <td className={styles.hideOnMobile}>{formatDate(row.created_at)}</td>
                  <td>{row.item_name}{row.amount > 1 ? ` ${row.amount} шт.` : ""}</td>
                  <td>
                    {Number(row.price).toFixed(2)} дт.
                    <div className={styles.mobileExtra}>
                      Налог: {Number(row.tax).toFixed(2)} дт.
                    </div>
                  </td>
                  <td className={styles.hideOnMobile}>{Number(row.tax).toFixed(2)} дт.</td>
                  <td>
                    {row.buyer_name}
                    <div className={styles.mobileExtra}>
                      {formatDate(row.created_at)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </div>
  );
}

export default SalesHistoryView;
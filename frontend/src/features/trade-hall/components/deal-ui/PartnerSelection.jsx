import { memo } from 'react';
import styles from "../DealsView.module.css";
import btn from "../../../../shared/styles/buttons.module.css";

export const PartnerSelection = memo(function PartnerSelection({
  nearbyPartners,
  selectedPartnerId,
  setSelectedPartnerId,
  isProcessing,
  handleSelectPartner,
}) {
  return (
    <div className={styles.rightColumn}>
      <div className={styles.borderBox}>
        <table className={styles.dealTable}>
          <thead><tr><th>Найти партнёра по сделке</th></tr></thead>
          <tbody>
            <tr>
              <td>
                <select className={styles.partnerSelect} value={selectedPartnerId} onChange={(e) => setSelectedPartnerId(e.target.value)} disabled={isProcessing}>
                  <option value="">- Персонажи рядом -</option>
                  {nearbyPartners.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
                <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={handleSelectPartner} disabled={!selectedPartnerId || isProcessing}>Выбрать</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
});
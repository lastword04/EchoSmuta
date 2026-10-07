import { memo } from 'react';
import { adaptItemForCard } from '../../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import styles from "../DealsView.module.css";
import btn from "../../../../shared/styles/buttons.module.css";
import { decimalInputHandler } from "../../../../shared/lib/validation/numberInput";

export const DealBackpack = memo(function DealBackpack({
  myItems,
  myResources,
  myDealItems,
  isItemAsset,
  resFree,
  moneyInput,
  setMoneyInput,
  selectedCurrency,
  setSelectedCurrency,
  hasGold,
  leftDisabled,
  getQty,
  setQty,
  handleAddMoney,
  handleAddItem,
  handleAddResource,
  openResource,
  setSelectedItem,
}) {
  return (
    <div className={styles.leftColumn}>
     

      <div className={styles.moneyRow}>
        <span className={styles.moneyLabel}>В сделку:</span>
        <input
          type="text" inputMode="decimal" placeholder="0" className={styles.moneyInput} 
          value={moneyInput}
          onChange={decimalInputHandler(setMoneyInput, 7, 2, { strip: true })}
          disabled={leftDisabled}
        />
        {hasGold ? (
          <select className={styles.currencySelect} value={selectedCurrency} onChange={(e) => setSelectedCurrency(e.target.value)} disabled={leftDisabled}>
            <option value="ducats">дт</option>
            <option value="gold">злт</option>
          </select>
        ) : (
          <span>дт</span>
        )}
        <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={handleAddMoney} disabled={leftDisabled}>Добавить</button>
      </div>

      <div className={styles.borderBox}>
        <table className={styles.dealTable}>
          <thead><tr><th>Вещи</th><th></th><th></th></tr></thead>
          <tbody>
            {myItems.map((item) => {
              const inDeal = myDealItems.some(di => isItemAsset(di) && di.inventory_item_id === item.id);
              return (
                <tr key={item.id}>
                  <td>
                    <span 
                      className={btn.clickableItemName}
                      onClick={() => {
                        const adapted = adaptItemForCard({
                          name: item.item?.name || item.item_slug, item_type: item.item?.item_type, slug: item.item?.slug,
                          price: item.item?.price, weight: item.item?.weight,
                          parameters: item.item?.parameters || {}, ability_parameters: item.item?.ability_parameters || {},
                          minimal_level: item.item?.minimal_level, race: item.item?.race,
                        });
                        setSelectedItem(adapted);
                      }}
                    >
                      {item.item?.name || item.item_slug}
                    </span>
                    {item.amount > 1 ? ` ${item.amount} шт.` : ""}
                  </td>
                  <td>
                    {item.item?.is_stackable && item.amount > 1 && !inDeal && (
                      <input type="number" min="1" max={item.amount} className={styles.qtyInput} value={getQty(item.id, item.amount)} onChange={(e) => setQty(item.id, e.target.value)} disabled={leftDisabled} />
                    )}
                  </td>
                  <td>
                    {!inDeal && (
                      <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={handleAddItem(item)} disabled={leftDisabled}>В сделку</button>
                    )}
                  </td>
                </tr>
              );
            })}
            {myResources.map((res) => {
              const free = resFree(res);
              return (
                <tr key={res.resource_slug}>
                  <td>
                    <span className={btn.clickableItemName} onClick={() => openResource(res.resource_slug)}>
                      {res.resource_name}
                    </span>
                    {' '}{res.amount} шт.
                  </td>
                  {free > 0 ? (
                    <>
                      <td>
                        <input type="number" min="1" max={free} className={styles.qtyInput} value={getQty(res.resource_slug, free)} onChange={(e) => setQty(res.resource_slug, e.target.value)} disabled={leftDisabled} />
                      </td>
                      <td>
                        <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={handleAddResource(res.resource_slug)} disabled={leftDisabled}>В сделку</button>
                      </td>
                    </>
                  ) : (
                    <td colSpan="2" />
                  )}
                </tr>
              );
            })}
            {myItems.length === 0 && myResources.length === 0 && (
              <tr><td colSpan="3" className={styles.empty}>Нет вещей в рюкзаке</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
});

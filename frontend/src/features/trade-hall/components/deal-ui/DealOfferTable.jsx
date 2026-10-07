import { memo } from 'react';
import { MoneyRow } from './MoneyRow';
import { AssetRow } from './AssetRow';
import styles from "../DealsView.module.css";

export const DealOfferTable = memo(function DealOfferTable({
  offer,
  items,
  isEditable,
  isProcessing,
  onRemoveDucats,
  onRemoveGold,
  onRemoveItem,
  onRemoveResource,
  onItemClick,
  onResourceClick,
  displayName,
  isItemAsset,
}) {
  const ducats = parseFloat(offer?.ducats_escrowed || 0);
  const gold = parseFloat(offer?.gold_escrowed || 0);
  const isEmpty = items.length === 0 && ducats === 0 && gold === 0;

  return (
    <div className={styles.borderBox}>
      <table className={styles.dealTable}>
        <thead>
          <tr>
            <th>Вещи</th>
            {isEditable && <th></th>}
          </tr>
        </thead>
        <tbody>
          {ducats > 0 && (
            <MoneyRow
              currency="ducats"
              amount={ducats}
              isEditable={isEditable}
              isProcessing={isProcessing}
              onRemove={onRemoveDucats}
            />
          )}
          {gold > 0 && (
            <MoneyRow
              currency="gold"
              amount={gold}
              isEditable={isEditable}
              isProcessing={isProcessing}
              onRemove={onRemoveGold}
            />
          )}
          {items.map((it) => (
            <AssetRow
              key={it.id}
              item={it}
              isEditable={isEditable}
              isProcessing={isProcessing}
              onItemClick={onItemClick}
              onResourceClick={onResourceClick}
              onRemoveItem={onRemoveItem}
              onRemoveResource={onRemoveResource}
              displayName={displayName}
              isItemAsset={isItemAsset}
            />
          ))}
          {isEmpty && (
            <tr>
              <td colSpan={isEditable ? 2 : 1} className={styles.empty}>
                Нет предметов для сделки
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
});
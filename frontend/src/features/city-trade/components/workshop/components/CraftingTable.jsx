// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useCallback, useMemo } from 'react';
import { ItemInfoCard } from '../../../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { getRaceName } from '../utils/raceMapper';
import { sortRecipesByOrder } from '../../../../../entities/items/config/recipeOrderConfig';
import { getLocationTexts } from '../../../config/locationTextConfig';
import styles from '../../WorkshopView.module.css';
import btn from '../../../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

export const CraftingTable = ({ startedCrafting, selectedStartCreatingId, onRecipeSelect, locationSlug, character, isCraftingInProgress }) => {
  
  // ── Конфигурация ──
  const texts = getLocationTexts(locationSlug);

  // ── State ──
  const [selectedItem, setSelectedItem] = useState(null);

  // ── Callbacks ──
  const handleItemClick = useCallback((recipe) => {
    if (recipe) setSelectedItem(adaptItemForCard(recipe));
  }, []);

  // ── Computed ──
  const sortedCrafting = useMemo(() => {
    if (!startedCrafting || startedCrafting.length === 0) return [];
    
    const craftingWithMeta = startedCrafting.map(r => ({
      ...r,
      slug: r.item_details?.item?.slug || '',
      name: r.item_details?.item?.name || '',
      minimal_level: r.item_details?.item?.minimal_level ?? 0,
    }));
    
    return sortRecipesByOrder(craftingWithMeta, locationSlug);
  }, [startedCrafting, locationSlug]);

    // ── Guards ──
  // Если данных нет (undefined из-за skip или null), мы ничего не рисуем.
  if (startedCrafting === undefined || startedCrafting === null) return null;

  // Если данные пришли, и это честный пустой массив — только тогда показываем сообщение.
  if (startedCrafting.length === 0) {
    return <div className={styles.noRecipes}>Нет начатого изготовления</div>;
  }

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.borderBox}>
      <table className={`${styles.recipesTable} ${texts.showRace ? styles.withRace : ''}`}>
        <colgroup>
          <col className={styles.colCheckbox} />
          <col className={styles.colElixir} />
          {texts.showRace && <col className={styles.colRace} />}
          <col className={styles.colDescription} />
          <col className={styles.colComponents} />
        </colgroup>
        <thead>
          <tr>
            <th className={styles.tableHeader}></th>
            <th className={styles.tableHeader}>{texts.workshopNameColumn}</th>
            {texts.showRace && <th className={`${styles.tableHeader} ${styles.hideOnMobile}`}>Раса</th>}
            <th className={styles.tableHeader}>Этап</th>
            <th className={styles.tableHeader}>Ресурсы</th>            
          </tr>
        </thead>
        <tbody>
          {sortedCrafting.map((recipe) => {
            const craftStage = recipe.craft_stage || 0;
            const totalStages = recipe.item_details?.item?.craft_stages || 0;
            const stagesText = `Этапов: ${craftStage}/${totalStages}`;

            return (
              <tr key={recipe.id} className={styles.recipeRow}>
                <td style={{ textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedStartCreatingId === recipe.id}
                    onChange={() => onRecipeSelect(recipe.id)}
                    className={styles.recipeCheckbox}
                    disabled={isCraftingInProgress}
                    title={
                      isCraftingInProgress 
                        ? 'Дождитесь завершения текущего крафта' 
                        : stagesText
                    }
                  />
                </td>
                <td>
                  <span 
                    className={btn.clickableItemName}
                    onClick={() => handleItemClick(recipe)}
                  >
                    {recipe.item_details?.item?.name || 'Неизвестно'}
                  </span>
                  {texts.showRace && (
                    <div className={styles.mobileExtra}>
                      {getRaceName(recipe.item_details?.item?.race)}
                    </div>
                  )}
                </td>
                {texts.showRace && (
                  <td className={styles.hideOnMobile}>
                    {getRaceName(recipe.item_details?.item?.race)}
                  </td>
                )}
                <td>
                  {(() => {
                    const stage = recipe.craft_stage || 0;
                    const total = recipe.item_details?.item?.craft_stages;
                    if (!total || total <= 1) return '-';
                    return `${stage}/${total}`;
                  })()}
                </td>
                <td>
                  {recipe.item_details?.components && recipe.item_details.components.length > 0 ? (
                    <div className={styles.components}>
                      {recipe.item_details.components.map((component, index) => (
                        <span
                          key={component.id || index}
                          className={component.is_in_stock ? styles.inStock : styles.outOfStock}
                        >
                          {component.resource_name} ({component.quantity})
                          {index < recipe.item_details.components.length - 1 ? ' ' : ''}
                        </span>
                      ))}
                    </div>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {selectedItem && (
        <div
          className={styles.itemCardOverlay}
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedItem(null);
          }}
        >
          <ItemInfoCard
            item={selectedItem}
            onClose={() => setSelectedItem(null)}
            character={character}
          />
        </div>
      )}
    </div>
  );
};
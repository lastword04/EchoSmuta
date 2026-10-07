// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useCallback, useMemo } from 'react';
import { ItemInfoCard } from '../../../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { formatRecipeDescription } from '../../../../../shared/lib/formatting/abilityParametersFormatter';
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

export const RecipesTable = ({ recipes, startedCrafting, selectedRecipe, onRecipeSelect, locationSlug, character, isCraftingInProgress }) => {
  
  // ── Конфигурация ──
  const texts = getLocationTexts(locationSlug);

  // ── State ──
  const [selectedItem, setSelectedItem] = useState(null);

  // ── Callbacks ──
  const handleItemClick = useCallback((recipe) => {
    if (recipe) setSelectedItem(adaptItemForCard(recipe));
  }, []);

  // ── Computed ──
  const sortedRecipes = useMemo(() => {
    if (!recipes || recipes.length === 0) return [];
    
    const recipesWithMeta = recipes.map(r => ({
      ...r,
      slug: r.item_details?.item?.slug || '',
      name: r.item_details?.item?.name || '',
      minimal_level: r.item_details?.item?.minimal_level ?? 0,
    }));
    
    return sortRecipesByOrder(recipesWithMeta, locationSlug);
  }, [recipes, locationSlug]);

    // ── Guards ──
  if (startedCrafting === undefined || startedCrafting === null) return null;
  if (recipes === undefined || recipes === null) return null;

  if (recipes.length === 0) {
    return <div className={styles.noRecipes}>{texts.noRecipesText}</div>;
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
            <th className={styles.tableHeader}>Описание</th>
            <th className={styles.tableHeader}>Ресурсы</th>
          </tr>
        </thead>
        <tbody>
          {sortedRecipes.map((recipe) => {
            const itemSlug = recipe.item_details?.item?.slug;
            
            // Проверяем, есть ли этот конкретный эликсир уже в списке активных крафтов
            const isCurrentlyCrafting = (startedCrafting || []).some(
              (sc) => sc.item_details?.item?.slug === itemSlug
            );

            return (
              <tr key={recipe.recipe_id} className={styles.recipeRow}>
                <td style={{ textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedRecipe === recipe.recipe_id}
                    onChange={() => onRecipeSelect(recipe.recipe_id)}
                    className={styles.recipeCheckbox}
                    // Отключаем галочку, если идет ЛЮБОЙ крафт, ИЛИ если этот рецепт уже варится
                    disabled={isCraftingInProgress || isCurrentlyCrafting}
                    title={
                      isCraftingInProgress 
                        ? 'Дождитесь завершения текущего крафта' 
                        : 'Начать крафт' // <-- Упрощенный тултип
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
                  {recipe.item_details?.item
                    ? formatRecipeDescription(recipe.item_details.item)
                    : '-'}
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
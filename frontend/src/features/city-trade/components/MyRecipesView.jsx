import { useState, useMemo, useRef } from "react";
import { useGetMyRecipesQuery } from "../../../entities/items/api/inventoryApi"; 
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { formatRecipeDescription } from "../../../shared/lib/formatting/abilityParametersFormatter";
import { sortRecipesByOrder } from '../../../entities/items/config/recipeOrderConfig';
import { getLocationTexts } from '../config/locationTextConfig';
import { getRaceName } from './workshop/utils/raceMapper';
import styles from "./MyRecipesView.module.css";
import btn from '../../../shared/styles/buttons.module.css'; 
import { DataState } from '../../../shared/ui/DataState/DataState';

function MyRecipesView({ locationSlug, character }) {  
  const texts = getLocationTexts(locationSlug);
  const [selectedItem, setSelectedItem] = useState(null);  
  const lastDataRef = useRef(null);

  // ═══ RTK QUERY ═══
  const { 
    data: myRecipes, 
    error, 
    isLoading, 
    refetch 
  } = useGetMyRecipesQuery(
    { locationSlug },
    { 
      skip: !locationSlug,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (myRecipes !== undefined && myRecipes !== null) {
    lastDataRef.current = myRecipes;
  }
  const displayMyRecipes = myRecipes !== undefined ? myRecipes : lastDataRef.current;
 

  // ═══ COMPUTED ═══
  const sortedRecipes = useMemo(() => {
    if (!displayMyRecipes) return null; // Пока isLoading === true
    if (!displayMyRecipes || displayMyRecipes.length === 0) return [];
    
    const recipesWithMeta = displayMyRecipes.map(r => ({
      ...r,
      slug: r.item_details?.item?.slug || '',
      name: r.item_details?.item?.name || '',
      minimal_level: r.item_details?.item?.minimal_level ?? 0,
    }));
    return sortRecipesByOrder(recipesWithMeta, locationSlug);
  }, [displayMyRecipes, locationSlug]);

  const getResources = (recipe) => {
    const components = recipe.item_details?.components || [];
    if (components.length === 0) return "—";
    return components.map(c => `${c.resource_name || c.resource_slug}: ${c.quantity}`).join(", ");
  };

  const getDescription = (recipe) => formatRecipeDescription(recipe.item_details?.item);

  // ═══ RENDER ═══
  if (sortedRecipes === null) return null; // Загрузка

  return (
    <div className={styles.recipesContainer}>
      <DataState
        error={!!error}
        errorMessage="Не удалось загрузить ваши рецепты"
        onRetry={refetch}
        isEmpty={sortedRecipes.length === 0}
        emptyMessage="У вас пока нет рецептов"
        isLoading={isLoading}
      >
        <div className={styles.borderBox}>
          <table className={`${styles.recipesTable} ${texts.showRace ? styles.withRace : ''}`}>
            <colgroup>
              <col />
              {texts.showRace && <col />}
              <col />
              <col />
            </colgroup>
            <thead>
              <tr>
                <th className={styles.tableHeader}>{texts.recipeColumn}</th>
                {texts.showRace && <th className={`${styles.tableHeader} ${styles.raceHeader}`}>Раса</th>}
                <th className={styles.tableHeader}>Описание</th>
                <th className={styles.tableHeader}>Ресурсы</th>
              </tr>
            </thead>
            <tbody>
              {sortedRecipes.map((recipe, index) => {
                const item = recipe.item_details?.item;
                return (
                  <tr key={recipe.recipe_id || index} className={styles.recipeRow}>
                    <td className={styles.recipeNameCell}>
                      <span 
                        className={btn.clickableItemName}
                        onClick={() => setSelectedItem(adaptItemForCard({ ...recipe, amount: recipe.quantity }))}
                      >
                        {item?.name || "Рецепт"}
                      </span>
                      <span className={styles.quantityBadge}> ({recipe.quantity})</span>
                      {texts.showRace && (
                        <div className={styles.mobileRace}>{getRaceName(item?.race)}</div>
                      )}
                    </td>
                    {texts.showRace && <td className={`${styles.raceCell} ${styles.hideOnMobile}`}>{getRaceName(item?.race)}</td>}
                    <td className={styles.descriptionCell}>{getDescription(recipe)}</td>
                    <td className={styles.resourcesCell}>{getResources(recipe)}</td>                 
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </DataState>
      
      {selectedItem && (
        <div
          className={styles.itemCardOverlay}
          onClick={(e) => { if (e.target === e.currentTarget) setSelectedItem(null); }}
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
}

export default MyRecipesView;
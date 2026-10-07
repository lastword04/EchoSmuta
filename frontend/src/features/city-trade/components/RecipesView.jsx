import { useState, useEffect, useMemo, useRef } from "react";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import { useGetRecipesQuery, useBuyRecipeMutation } from "../../../entities/items/api/inventoryApi"; 
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import { formatRecipeDescription } from "../../../shared/lib/formatting/abilityParametersFormatter";
import { sortRecipesByOrder } from '../../../entities/items/config/recipeOrderConfig';
import { getLocationTexts } from '../config/locationTextConfig';
import { getRaceName } from './workshop/utils/raceMapper';
import styles from "./RecipesView.module.css";
import btn from '../../../shared/styles/buttons.module.css'; 
import { DataState } from '../../../shared/ui/DataState/DataState';


// ═══ КОНСТАНТЫ ═══
const DEFAULT_QUANTITY_OPTIONS = [1, 5, 10];
// ... (константы ITEM_TYPE_TO_CATEGORY, CATEGORY_DISPLAY_ORDER, SUBCATEGORY_CONFIG, getSubcategory оставляем без изменений) ...
const ITEM_TYPE_TO_CATEGORY = { weapon: "Оружие", shield: "Щиты", kit: "Броня", helmet: "Броня", armor: "Броня", gauntlets: "Броня", gloves: "Броня", leggings: "Броня", boots: "Броня", cloak: "Плащи", amulet: "Амулеты", pendant: "Кулоны", ring: "Кольца" };
const CATEGORY_DISPLAY_ORDER = ["Оружие", "Щиты", "Броня", "Плащи", "Амулеты", "Кулоны", "Кольца"];
const SUBCATEGORY_CONFIG = {
  "Оружие": [{ id: "swords", label: "Мечи" }, { id: "axes", label: "Топоры" }, { id: "hammers", label: "Молоты" }],
  "Броня": [{ id: "helmet", label: "Шлемы" }, { id: "armor", label: "Доспехи" }, { id: "gauntlets", label: "Нарукавники" }, { id: "gloves", label: "Перчатки" }, { id: "leggings", label: "Поножи" }, { id: "boots", label: "Сандалии" }, { id: "kit", label: "Комплекты" }],
};
const getSubcategory = (recipe) => {
  const type = recipe.item_type;
  const slug = recipe.slug || '';
  if (type === 'weapon') { if (slug.includes('axe')) return 'axes'; if (slug.includes('hammer')) return 'hammers'; return 'swords'; }
  if (type === 'kit') return 'kit';
  if (['helmet', 'armor', 'gauntlets', 'gloves', 'leggings', 'boots'].includes(type)) { if (slug.endsWith('-kit')) return 'kit'; return type; }
  return null;
};

function RecipesView({ locationSlug, character }) {
  const locationConfig = getTradeLocationConfig(locationSlug);
  const quantityOptions = locationConfig?.quantityOptions || DEFAULT_QUANTITY_OPTIONS;
  const isProduction = locationConfig?.isProduction;
  const texts = getLocationTexts(locationSlug);
  const { currentError, showError } = useErrorToast();
  const lastDataRef = useRef(null); 
  
  const [buyRecipe] = useBuyRecipeMutation();

  const [selectedQuantity, setSelectedQuantity] = useState(quantityOptions[0]);  
  const [isBuying, setIsBuying] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState("ALL");
  const [selectedCategory, setSelectedCategory] = useState("Все категории");
  const [selectedSubcategory, setSelectedSubcategory] = useState("ALL");
  const [selectedItem, setSelectedItem] = useState(null);
  const [isRefreshingQuantity, setIsRefreshingQuantity] = useState(false); 

  // ═══ RTK QUERY ═══
  const { 
    data: recipes, 
    error: recipesErrorObj, 
    isFetching: isRecipesLoading,
    refetch
  } = useGetRecipesQuery(
    { quantity: selectedQuantity, locationSlug },
    { 
      skip: !locationSlug,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (recipes !== undefined && recipes !== null) {
    lastDataRef.current = recipes;
  }
  const displayRecipes = recipes !== undefined ? recipes : lastDataRef.current;
 

  // Сброс фильтров при смене локации
  useEffect(() => {
    setSelectedQuantity(quantityOptions[0]);
    setSelectedLevel("ALL");
    setSelectedCategory("Все категории");
    setSelectedSubcategory("ALL");    
  }, [locationSlug, quantityOptions]);

  // ═══ COMPUTED ═══
  const categoryOptions = useMemo(() => {
    if (!isProduction) return ["Все категории"];
    const present = new Set();
    (displayRecipes || []).forEach(r => {
      const cat = ITEM_TYPE_TO_CATEGORY[r.item_type];
      if (cat) present.add(cat);
    });
    return ["Все категории", ...CATEGORY_DISPLAY_ORDER.filter(c => present.has(c))];
  }, [displayRecipes, isProduction]);

  const subcategoryOptions = SUBCATEGORY_CONFIG[selectedCategory] || [];

  const availableLevels = useMemo(() => {
    if (!displayRecipes) return [];
    const levels = new Set(displayRecipes.map(r => r.minimal_level).filter(Boolean));
    return Array.from(levels).sort((a, b) => a - b);
  }, [displayRecipes]);

  const filteredRecipes = useMemo(() => {
    if (!displayRecipes) return [];
    let filtered = displayRecipes.filter(recipe => {
      if (!recipe) return false;
      if (selectedLevel !== "ALL" && recipe.minimal_level !== Number(selectedLevel)) return false;
      if (selectedCategory !== "Все категории") {
        const itemType = recipe.item_type;
        if (!itemType) return false;
        if (ITEM_TYPE_TO_CATEGORY[itemType] !== selectedCategory) return false;
        if (selectedSubcategory !== "ALL" && getSubcategory(recipe) !== selectedSubcategory) return false;
      }
      return true;
    });
    return sortRecipesByOrder(filtered, locationSlug);
  }, [displayRecipes, selectedLevel, selectedCategory, selectedSubcategory, locationSlug]);

  // ═══ HANDLERS ═══
  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
    setSelectedSubcategory("ALL");
  };

  const handleQuantityClick = (option) => {
    if (option === selectedQuantity) {
      // Защита от спама: если уже идёт рефреш — игнорируем клик
      if (isRefreshingQuantity) return;      
      setIsRefreshingQuantity(true);
      refetch();      
      // Через 300мс сбрасываем визуальное состояние
      setTimeout(() => {
        setIsRefreshingQuantity(false);
      }, 300);
    } else {
      setSelectedQuantity(option);
    }
  };

  const handleBuyRecipe = async (recipe) => {
    if (isBuying) return;
    setIsBuying(recipe.id);
    try {
      const itemSlug = recipe.slug || recipe.item_slug;
      if (!itemSlug) { showError("Не удалось определить рецепт"); return; }
      
      await buyRecipe({ itemSlug, quantity: selectedQuantity }).unwrap();
      // ↑↑↑ loadRecipes УДАЛЕН. RTK Query сам обновит список благодаря invalidatesTags!
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = "Произошла ошибка при покупке рецепта";
      if (errorData?.error_code === "NOT_ENOUGH_DUCATS") {
        errorMessage = `Недостаточно средств. Требуется: ${errorData.extras?.required_ducats || '?'} дт.`;
      } else if (errorData?.error_code === "RECIPE_ALREADY_EXISTS") {
        errorMessage = "У вас уже есть этот рецепт";
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setIsBuying(null);
    }
  };

  // ═══ RENDER ═══
  if (!displayRecipes && isRecipesLoading) return null;

  return (
    <div className={styles.recipesContainer}>
      <ErrorToast message={currentError} />
      
      <div className={styles.quantitySelector}>
        <span className={styles.quantityLabel}>
          {texts.recipeActionPrefix}{' '}
          {quantityOptions.map((option, index) => (
            <span key={option}>
              <button className={`${btn.gameButton} ${btn.sizeSmall} ${selectedQuantity === option ? btn.gameButtonActive : ''}`}
                onClick={() => handleQuantityClick(option)} disabled={isRefreshingQuantity}>
                {option}
              </button>              
              {index < quantityOptions.length - 1 && <span className={styles.separator}> • </span>}
            </span>
          ))}
          {' '}{texts.recipeUnit}
        </span>
      </div>

      {isProduction && (
        <div className={styles.filters}>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Уровень</label>
            <select className={styles.filterSelect} value={selectedLevel} onChange={e => setSelectedLevel(e.target.value)}>
              <option value="ALL">Все уровни</option>
              {availableLevels.map(lvl => <option key={lvl} value={lvl}>{lvl}</option>)}
            </select>
          </div>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Категория</label>
            <select className={styles.filterSelect} value={selectedCategory} onChange={handleCategoryChange}>
              {categoryOptions.map(label => <option key={label} value={label}>{label}</option>)}
            </select>
          </div>
          {subcategoryOptions.length > 0 && (
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Тип</label>
              <select className={styles.filterSelect} value={selectedSubcategory} onChange={e => setSelectedSubcategory(e.target.value)}>
                <option value="ALL">Все</option>
                {subcategoryOptions.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
              </select>
            </div>
          )}
        </div>
      )}

      <DataState
        error={!!recipesErrorObj}
        errorMessage="Не удалось загрузить рецепты"
        onRetry={refetch}
        isEmpty={filteredRecipes.length === 0}
        emptyMessage="Рецепты не найдены"
        isLoading={!recipes && isRecipesLoading}
      >
        <div className={styles.borderBox}>
          <table className={`${styles.recipesTable} ${texts.showRace ? styles.withRace : ''}`}>
            <colgroup>
              <col className={styles.colRecipe} />
              {texts.showRace && <col className={styles.colRace} />}
              <col className={styles.colDescription} />
              <col className={styles.colPrice} />
              <col className={styles.colAction} />
            </colgroup>
            <thead>
              <tr>
                <th className={styles.tableHeader}>{texts.recipeColumn}</th>
                {texts.showRace && <th className={`${styles.tableHeader} ${styles.hideOnMobile}`}>Раса</th>}
                <th className={styles.tableHeader}>Описание</th>
                <th className={`${styles.tableHeader} ${styles.hideOnMobile}`}>Цена</th>
                <th className={styles.tableHeader}></th>
              </tr>
            </thead>
            <tbody>
              {filteredRecipes.map((recipe, index) => (
                <tr key={recipe.id || index} className={styles.recipeRow}>
                  <td className={styles.recipeNameCell}>
                    <span className={btn.clickableItemName} onClick={() => setSelectedItem(adaptItemForCard(recipe))}>
                      {recipe.name}
                    </span>
                    {texts.showRace && <div className={styles.mobileExtra}>{getRaceName(recipe.race)}</div>}
                  </td>
                  {texts.showRace && <td className={styles.hideOnMobile}>{getRaceName(recipe.race)}</td>}
                  <td className={styles.descriptionCell}>{formatRecipeDescription(recipe)}</td>
                  <td className={styles.hideOnMobile}>{recipe.recipe_price ? `${recipe.recipe_price} дт.` : "—"}</td>
                  <td className={styles.actionCell}>
                    <button 
                      className={`${btn.textLinkDanger} ${styles.buyButtonOverride}`} 
                      onClick={() => handleBuyRecipe(recipe)} 
                      disabled={isBuying === recipe.id}
                    >
                      Купить
                    </button>
                    <div className={styles.mobileBuy}>{recipe.recipe_price ? `${recipe.recipe_price} дт.` : "—"}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
      
      {selectedItem && (
        <div className={styles.itemCardOverlay} onClick={(e) => { if (e.target === e.currentTarget) setSelectedItem(null); }}>
          <ItemInfoCard item={selectedItem} onClose={() => setSelectedItem(null)} character={character} />
        </div>
      )}
    </div>
  );
}

export default RecipesView;
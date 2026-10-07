import { useState } from "react";
import {
  useGetAdminItemTypesQuery,
  useListAdminItemsQuery,
} from "../../../../entities/admin/api";
import styles from "../../AdminPage.module.css";

export default function ItemsCatalogTab() {
  const [selectedType, setSelectedType] = useState("");
  const [search, setSearch] = useState("");

  const { data: itemTypes = [], error: typesError } = useGetAdminItemTypesQuery();
  const { data: itemsResult, isLoading, error: itemsError } = useListAdminItemsQuery({
    item_type: selectedType || undefined,
    search: search.trim() || undefined,
    limit: 100,
  });

  const items = itemsResult?.objects || [];
  const error = typesError?.data?.detail || itemsError?.data?.detail || "";

  return (
    <div>
      <div className={styles.catalogTabs}>
        <button className={selectedType === "" ? styles.active : ""} onClick={() => setSelectedType("")}>Все</button>
        {itemTypes.map((type) => (
          <button
            key={type.item_type}
            className={selectedType === type.item_type ? styles.active : ""}
            onClick={() => setSelectedType(type.item_type)}
          >
            {type.readable_name}
          </button>
        ))}
      </div>
      <div className={styles.filters}>
        <input
          type="search"
          placeholder="Поиск по названию или slug"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      {error && <div className={styles.error}>{error}</div>}
      <table className={styles.table}>
        <thead><tr><th>Название</th><th>Slug</th><th>Тип</th><th>Локация</th><th>Цена</th><th>Вес</th><th>Мин. уровень</th><th>Stackable</th></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td><td>{item.slug}</td><td>{item.item_type}</td><td>{item.location_slug || "—"}</td>
              <td>{item.price}</td><td>{item.weight}</td><td>{item.minimal_level}</td><td>{item.is_stackable ? "Да" : "Нет"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!isLoading && items.length === 0 && <div className={styles.empty}>Предметы не найдены</div>}
    </div>
  );
}
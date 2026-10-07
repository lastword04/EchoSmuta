import { useState } from "react";
import {
  useGetAdminResourceCategoriesQuery,
  useListAdminResourcesQuery,
} from "../../../../entities/admin/api";
import styles from "../../AdminPage.module.css";

export default function ResourcesCatalogTab() {
  const [selectedCategory, setSelectedCategory] = useState("");

  const { data: categories = [], error: catError } = useGetAdminResourceCategoriesQuery();
  const { data: resourcesResult, isLoading, error: resError } = useListAdminResourcesQuery({
    category: selectedCategory || undefined,
    limit: 100,
  });

  const resources = resourcesResult?.objects || [];
  const error = catError?.data?.detail || resError?.data?.detail || "";

  return (
    <div>
      <div className={styles.catalogTabs}>
        <button className={selectedCategory === "" ? styles.active : ""} onClick={() => setSelectedCategory("")}>Все</button>
        {categories.map((category) => (
          <button
            key={category.category}
            className={selectedCategory === category.category ? styles.active : ""}
            onClick={() => setSelectedCategory(category.category)}
          >
            {category.readable_name}
          </button>
        ))}
      </div>
      {error && <div className={styles.error}>{error}</div>}
      <table className={styles.table}>
        <thead><tr><th>Название</th><th>Slug</th><th>Категория</th><th>Цена</th><th>Вес</th><th>Серийный номер</th></tr></thead>
        <tbody>
          {resources.map((resource) => (
            <tr key={resource.id}>
              <td>{resource.name}</td><td>{resource.slug}</td><td>{resource.category || "—"}</td>
              <td>{resource.price}</td><td>{resource.weight}</td><td>{resource.serial_number}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!isLoading && resources.length === 0 && <div className={styles.empty}>Ресурсы не найдены</div>}
    </div>
  );
}
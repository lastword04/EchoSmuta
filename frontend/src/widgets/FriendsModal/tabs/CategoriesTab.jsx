import React from "react";
import styles from "../FriendsModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const CategoriesTab = ({
  detailedCategories,
  newCategoryName,
  setNewCategoryName,  
  categoryError,
  categorySuccess,
  onCreate,
  onDelete,
  onCheckboxChange,  
  checkboxError,  
  isCreating,
  deletingCategoryId,
  updatingCheckboxId,
}) => {
  const userCategories = detailedCategories.filter(
    (c) => !["Друзья", "Враги"].includes(c.name)
  );

  return (
    <div className={styles.categoriesTab}>
      {checkboxError && (
        <div className={styles.errorText}>{checkboxError}</div>
      )}
      {detailedCategories.length === 0 ? (
        <div className={styles.placeholder}>Нет категорий</div>
      ) : (
        <>
          {/* Блок Друзья и Враги */}
          <div className={styles.primaryCategoriesBlock}>
            <table className={styles.permissionTable}>
              <tbody>
                <tr>
                  <td className={styles.sectionTitle}>Разрешение уведомлений</td>
                  {["Друзья", "Враги"].map((name) => {
                    const cat = detailedCategories.find((c) => c.name === name);
                    return (
                      <td key={name} className={styles.categoryHeaderCell}>
                        <div className={styles.mainCategoryHeaderWrapper}>
                          <strong>{cat?.name || name}</strong>
                          {cat && (
                            <span className={styles.categoryCount}>
                              ({cat.characters_count}/{cat.max_count_characters})
                            </span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>

                {[
                  { label: "Получение", field: "is_receive_notifications" },
                  { label: "Отправка", field: "is_send_notifications" },
                  { label: "Запрет отправки писем", field: "is_block_send_mails" },
                ].map(({ label, field }) => (
                  <tr key={field}>
                    <td className={styles.permissionLabel}>{label}</td>
                    {["Друзья", "Враги"].map((name) => {
                      const cat = detailedCategories.find((c) => c.name === name);
                      return (
                        <td key={name} className={styles.checkboxCell}>
                          <input
                            type="checkbox"
                            checked={cat?.[field] || false}
                            onChange={(e) =>
                              cat && onCheckboxChange(cat.id, field, e.target.checked)
                            }              
                            disabled={updatingCheckboxId === cat?.id}              
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Остальные категории */}
          {userCategories.length > 0 && (
            <div className={styles.secondaryCategoriesBlock}>
              <table className={styles.permissionTable}>
                <tbody>
                  <tr>
                    <td></td>
                    <td className={styles.categoryHeaderCell}>
                      <strong>Запрет отправки писем</strong>
                    </td>
                  </tr>

                  {userCategories.map((cat) => (
                    <tr key={cat.id}>
                      <td className={styles.permissionLabel}>
                        <div className={styles.categoryHeaderWrapper}>
                          <span>
                            <strong>{cat.name}</strong>{" "}
                            <span className={styles.categoryCount}>
                              ({cat.characters_count}/{cat.max_count_characters})
                            </span>
                          </span>
                          <button
                            className={btn.textLinkDanger}
                            onClick={() => onDelete(cat.id)}     
                            disabled={deletingCategoryId === cat.id}                       
                          >
                            ✕
                          </button>
                        </div>
                      </td>
                      <td className={styles.checkboxCell}>
                        <input
                          type="checkbox"
                          checked={cat.is_block_send_mails || false}
                          onChange={(e) =>
                            onCheckboxChange(cat.id, "is_block_send_mails", e.target.checked)
                          }          
                          disabled={updatingCheckboxId === cat.id}               
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Добавление новой категории */}
      {detailedCategories.length < 5 && (
        <div className={styles.newCategory}>
          <div className={styles.newCategoryTitle}>Новая категория</div>
          <div className={styles.newCategoryRow}>
            <input
              type="text"
              placeholder="Название категории"
              className={styles.newCategoryInput}
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              maxLength={25}
            />
            <button
              className={btn.accentButton}
              onClick={onCreate}
              disabled={!newCategoryName.trim() || isCreating}
            >
              Добавить
            </button>
          </div>

          {categoryError && <div className={styles.addError}>{categoryError}</div>}
          {categorySuccess && <div className={styles.successText}>{categorySuccess}</div>}
        </div>
      )}
    </div>
  );
};

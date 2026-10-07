import React from "react";
import styles from "./ResourceInfoCard.module.css";

export const ResourceInfoCard = ({ resource, onClose }) => {
  if (!resource) return null;

  return (
    <div className={styles.resourceInfoCard}>
      <div className={styles.resourceInfoHeader}>
        <div className={styles.resourceInfoTitle}>{resource.name}</div>
        <button className={styles.resourceInfoClose} onClick={onClose}>✕</button>
      </div>

      {/* Верхняя строка с ценой и весом (как в ItemInfoCard) */}
      <div className={styles.resourceInfoTopRow}>
        <span className={styles.priceLeft}>Цена: <b>{resource.price}</b> дт.</span>
        <span className={styles.weightCenter}>Вес: <b>{resource.weight}</b></span>
        <span className={styles.emptyRight}></span> {/* для баланса */}
      </div>

      {/* Блок с картинкой (теперь снизу) */}
      <div className={styles.resourceInfoImageBox}>
        <img
          className={styles.resourceInfoImage}
          src={`/images/resources/${resource.slug}.png`}
          alt={resource.name}
          onError={(e) => { e.target.style.display = 'none'; }}
          fetchPriority="high"
        />
      </div>
    </div>
  );
};
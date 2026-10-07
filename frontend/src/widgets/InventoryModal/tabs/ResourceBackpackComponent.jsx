import React from "react";
import { useResourceInfo } from "../../../entities/resources/hooks/useResourceInfo";
import { ResourceInfoCard } from "../../../entities/resources/ui/ResourceInfoCard/ResourceInfoCard";
import styles from "../InventoryModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const ResourceBackpackComponent = ({ resources }) => {
  const { selectedResource, openResource, closeResource } = useResourceInfo(resources);

  if (!resources || resources.length === 0)
    return <div className={styles.placeholder}>Ресурсов нет</div>;

  return (
    <div className={styles.resourceWrapper}>
      {selectedResource && (
        <ResourceInfoCard
          resource={selectedResource}
          onClose={closeResource}
        />
      )}
      <div className={styles.resourceList}>
        {resources.map((res) => (
          <div key={res.resource_slug} className={styles.resourceRow}>
            <div className={styles.resourceName}>
              <span
                className={btn.textLinkAction}
                onClick={() => openResource(res.resource_slug)}
              >
                {res.resource_name}
              </span>
              <span className={styles.resourceAmount}> {res.amount} шт.</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
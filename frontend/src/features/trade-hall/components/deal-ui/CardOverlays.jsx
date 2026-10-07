import { memo } from 'react';
import { ItemInfoCard } from '../../../../entities/items/ui/ItemInfoCard';
import { ResourceInfoCard } from '../../../../entities/resources/ui/ResourceInfoCard/ResourceInfoCard';
import styles from "../DealsView.module.css";

export const CardOverlays = memo(function CardOverlays({ 
  selectedItem, 
  selectedResource, 
  character, 
  onCloseItem, 
  onCloseResource 
}) {
  return (
    <>
      {selectedItem && (
        <div
          className={styles.itemCardOverlay}
          onClick={(e) => { if (e.target === e.currentTarget) onCloseItem(); }}
        >
          <ItemInfoCard
            item={selectedItem}
            onClose={onCloseItem}
            character={character}
          />
        </div>
      )}
      {selectedResource && (
        <div
          className={styles.itemCardOverlay}
          onClick={(e) => { if (e.target === e.currentTarget) onCloseResource(); }}
        >
          <ResourceInfoCard
            resource={selectedResource}
            onClose={onCloseResource}
          />
        </div>
      )}
    </>
  );
});
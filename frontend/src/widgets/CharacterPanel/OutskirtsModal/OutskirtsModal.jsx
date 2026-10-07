import { locations } from '../../../shared/config/locations/locations';
import { useMediaQuery } from '../../../shared/hooks/ui/useMediaQuery';
import styles from './OutskirtsModal.module.css';

export const OutskirtsModal = ({ onClose, handleLocationChange, setActiveModal }) => {
  const isMobile = useMediaQuery('(max-width: 1280px)');

  const handleClick = async (loc) => {
    if (!loc || loc.empty) return;

    // Карта города
    if (loc.noSlug) {
      onClose();
      setActiveModal("CITY_MAP_MODAL");
      return;
    }

    if(loc.name === "Авалон"){
      await handleLocationChange("1.17.station");
      return;
    }

    if (loc.slug) {
      await handleLocationChange(loc.slug);
    }
  };

  const resourceLocations = locations.resources;

  const cityMapItem = { name: 'Карта города', noSlug: true };


  /* ✦ Мобильные два столбца ✦ */
  const leftColumn = resourceLocations.filter((loc) => loc.position === "left" && loc.name !== 'Местоположение');
  
  const rightColumn = resourceLocations.filter((loc) => loc.position === "right" || loc.name === 'Местоположение');

  const renderItem = (loc, key) => {
    if (loc.empty) return <div key={key} className={styles.spacer} />;

     return (
      <div
        key={key}
        className={`${styles.location} ${
          loc.name === 'Местоположение' ? styles.currentLocation : ''
        }`}
        onClick={() => handleClick(loc)}
      >
        {loc.name}
      </div>
    );
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.content}>

          <div className={styles.leftPanel}>
            <div className={styles.mapContainer}>
            <img 
              src="/images/widgets/character-panel/outskirts-modal/map.png" 
              className={styles.mapImage} 
              alt="Карта" 
              fetchPriority="high"
              loading="eager"
            />
              <div className={styles.blinkingDot}></div>
            </div>
          </div>

          <div className={styles.header}>
            {isMobile && (
              <div
                className={`${styles.location} ${styles.clickableLocation} ${styles.cityMap}`}
                onClick={() => handleClick(cityMapItem)}
              >
                Карта города
              </div>
            )}
            <button className={styles.closeButton} onClick={onClose}>
              ✕
            </button>
          </div>

          <div className={styles.rightPanel}>
            <div className={styles.locationsList}>
              {!isMobile && (
                <div
                  className={`${styles.location} ${styles.clickableLocation}`}
                  onClick={() => handleClick(cityMapItem)}
                >
                  Карта города
                </div>
              )}
              {isMobile ? (
                <div className={styles.mobileColumns}>
                  <div className={styles.mobileColumn}>
                    {leftColumn.map((loc, i) => renderItem(loc, 'L-' + i))}
                  </div>
                  <div className={styles.mobileColumn}>
                    {rightColumn.map((loc, i) => renderItem(loc, 'R-' + i))}
                  </div>
                </div>
              ) : (
                resourceLocations.map((loc, i) => renderItem(loc, i))
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

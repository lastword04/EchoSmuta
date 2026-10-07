
import { locations } from '../../../shared/config/locations/locations';
import styles from './CityMapModal.module.css';

export const CityMapModal = ({ onClose, handleLocationChange, counts, setActiveModal }) => {

  const handleLocationClick = async (locationSlug, locationName) => {
    if (locationName === 'Окрестности') {
      onClose();
      setActiveModal("OUTSKIRTS_MODAL");
      return;
    }
    
    // Модалка закроется через setActiveModal(null) внутри handleLocationChange
    await handleLocationChange(locationSlug);
  };


  const getLocationName = (item) => {
    const count = counts?.[item.slug] || 0;  // ← optional chaining: если counts null, вернёт undefined, а || 0 даст 0
    return count > 0 ? `${item.name} (${count})` : item.name;
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.topScroll}>
          <div className={styles.header}>
            <button className={styles.closeButton} onClick={onClose}>
              ✕
            </button>
          </div>
        </div>

        <div className={styles.contentWrapper}>
          <div className={styles.content}>
            <div className={styles.cityTitle}>
              <span 
                className={styles.clickableLocation}
                onClick={() =>  console.log('working')}
              >
                Замок Порядка
              </span>
              <span className={styles.separator}>•</span>
              <span>Авалон</span>
              <span className={styles.separator}>•</span>
              <span 
                className={styles.clickableLocation}
                onClick={() => handleLocationClick(null, 'Окрестности')}
              >
                Окрестности
              </span>
            </div>
          
            <div className={styles.locationsContainer}>
              {locations.city.map((section, sectionIndex) => (
                <div key={sectionIndex} className={styles.section}>
                  <div className={styles.sectionTitle}>
                    {section.title}
                  </div>
                  <div className={styles.locationsList}>
                    {section.items.map((item, locationIndex) => (
                       <div
                        key={locationIndex}
                        className={`${styles.location} ${styles.clickable}`}
                        onClick={() => handleLocationClick(item.slug, item.name)}
                      >
                        {getLocationName(item)}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.bottomScroll}></div>
      </div>
    </div>
  );
};
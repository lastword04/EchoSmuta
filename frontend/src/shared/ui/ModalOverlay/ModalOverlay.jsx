import styles from './ModalOverlay.module.css';

/**
 * Единый оверлей для всех модалок.
 * inOutskirts — полноэкранный режим (Окрестности / карта из resource-локации).
 */
export const ModalOverlay = ({ inOutskirts, panelHeight, onClose, children }) => {
  return (
    <div
      className={inOutskirts ? styles.outskirtsOverlay : styles.modalOverlay}
      style={{ height: `calc(100vh - ${panelHeight}vh)` }}
      onClick={onClose}
    >
      <div className={inOutskirts ? styles.outskirtsContent : styles.modalContent}>
        {children}
      </div>
    </div>
  );
};

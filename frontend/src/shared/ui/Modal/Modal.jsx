import { useEffect } from 'react';
import styles from './Modal.module.css';

export const Modal = ({ isOpen, onClose, children }) => {
  // Закрываем модальное окно при нажатии Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Запрещаем скролл основного контента при открытом модальном окне
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Не рендерим ничего, если модальное окно закрыто
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    // Закрываем модальное окно только при клике на бэкдроп
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        {children}
      </div>
    </div>
  );
};
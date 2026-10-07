import styles from './DataState.module.css';
import btn from '../../styles/buttons.module.css';

/**
 * Универсальный обёрточный компонент для состояний загрузки данных.
 * Обрабатывает три состояния: error, empty, data.
 * Без спиннеров (loading обрабатывается родителем или return null).
 *
 * @param {boolean} error - есть ли ошибка
 * @param {string} errorMessage - текст ошибки (опционально)
 * @param {Function} onRetry - функция повторной загрузки (опционально)
 * @param {boolean} isEmpty - пусто ли данных (false по умолчанию)
 * @param {string} emptyMessage - текст при пустых данных
 * @param {React.ReactNode} children - контент при наличии данных
 */
export const DataState = ({
  error,
  errorMessage = "Не удалось загрузить данные",
  onRetry,
  isEmpty = false,
  emptyMessage = "Данных нет",
  children,
}) => {
  // Приоритет: error > empty > data
  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.message}>{errorMessage}</div>
        {onRetry && (
          <button 
            className={`${btn.gameButton} ${btn.sizeSmall}`}
            onClick={onRetry}
          >
            Повторить
          </button>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={styles.container}>
        <div className={styles.message}>{emptyMessage}</div>
      </div>
    );
  }

  return children;
};
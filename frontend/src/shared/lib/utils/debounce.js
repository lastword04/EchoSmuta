/**
 * Дебаунс для функций — откладывает выполнение до тех пор,
 * пока не пройдёт `wait` миллисекунд с последнего вызова.
 * 
 * @param {Function} func - функция для дебаунса
 * @param {number} wait - задержка в миллисекундах
 * @returns {Function} - дебаунснутая функция
 */
export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};
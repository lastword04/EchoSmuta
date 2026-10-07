import styles from './Select.module.css';

export const Select = ({ 
  label, 
  options, 
  value, 
  onChange, 
  placeholder,
  error,
  className = '',
  ...props 
}) => {
  return (
    <div className={`${styles.selectWrapper} ${className}`}>
      {label && (
        <label className={styles.label}>
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        className={`${styles.select} ${error ? styles.error : ''}`}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
};
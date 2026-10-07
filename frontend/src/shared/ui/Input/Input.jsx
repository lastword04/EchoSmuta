import styles from './Input.module.css';

export const Input = ({ 
  label, 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  error,
  className = '',
  ...props 
}) => {
  return (
    <div className={`${styles.inputWrapper} ${className}`}>
      {label && (
        <label className={styles.label}>
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={`${styles.input} ${error ? styles.error : ''}`}
        {...props}
      />
      {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
  );
};
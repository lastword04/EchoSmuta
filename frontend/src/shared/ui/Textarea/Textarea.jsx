import { forwardRef } from 'react';
import styles from './Textarea.module.css';

export const Textarea = forwardRef(({
  label,
  name,
  value = '',
  placeholder = '',
  onChange,
  onBlur,
  onFocus,
  error,
  disabled = false,
  required = false,
  rows = 4,
  cols,
  maxLength,
  minLength,
  resize = 'vertical', // 'none', 'both', 'horizontal', 'vertical'
  helperText,
  className = '',
  ...props
}, ref) => {
  const textareaId = `textarea-${name || Math.random().toString(36).substr(2, 9)}`;
  
  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    }
  };

  const textareaClasses = [
    styles.textarea,
    error ? styles.error : '',
    disabled ? styles.disabled : '',
    className
  ].filter(Boolean).join(' ');

  const containerClasses = [
    styles.container,
    disabled ? styles.containerDisabled : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses}>
      {label && (
        <label 
          htmlFor={textareaId} 
          className={styles.label}
        >
          {label}
        </label>
      )}
      
      <div className={styles.textareaWrapper}>
        <textarea
          ref={ref}
          id={textareaId}
          name={name}
          value={value}
          placeholder={placeholder}
          onChange={handleChange}
          onBlur={onBlur}
          onFocus={onFocus}
          disabled={disabled}
          required={required}
          rows={rows}
          cols={cols}
          maxLength={maxLength}
          minLength={minLength}
          className={textareaClasses}
          style={{ resize }}
          {...props}
        />
      </div>

      <div className={styles.footer}>
        {error && (
          <span className={styles.errorText}>
            {error}
          </span>
        )}
        
        {helperText && !error && (
          <span className={styles.helperText}>
            {helperText}
          </span>
        )}
      </div>
    </div>
  );
});

Textarea.displayName = 'Textarea';
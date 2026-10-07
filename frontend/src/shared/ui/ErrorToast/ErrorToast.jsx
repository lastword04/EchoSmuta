import styles from './ErrorToast.module.css';

const ErrorToast = ({ message, variant = 'default' }) => {
  if (!message) return null;
  return <div className={`${styles.errorToast} ${styles[variant]}`}>{message}</div>;
};

export default ErrorToast;
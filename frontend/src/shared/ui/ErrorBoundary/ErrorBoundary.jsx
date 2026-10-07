import React from 'react';
import styles from './ErrorBoundary.module.css';
import btn from '../../styles/buttons.module.css';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) this.props.onReset();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.container}>
          <div className={styles.message}>
            Что-то пошло не так при отображении блока
          </div>
          <button
            className={`${btn.gameButton} ${btn.sizeSmall}`}
            onClick={this.handleReset}
          >
            Повторить
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
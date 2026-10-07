/**
 * withBaseMainPage — презентационный HOC для публичных (не-игровых) страниц.
 *
 * Добавляет только общий фон (background.jpg) и min-height: 100vh.
 * Никакой бизнес-логики, состояния, WebSocket'ов или Redux.
 *
 * Потребители (15+): HomePage, LoginPage, RegisterPage, CharacterCreationPage,
 * CharacterAttachmentPage, ForumPage, ForumTopicsPage, TopicCommentsPage,
 * CreateTopicPage, ConfirmResetPasswordPage, ResetPasswordPage, ReferralsPage,
 * CharacterTransferPage, CharacterDetachmentPage и т.д.
 *
 * НЕ путать с `app/providers/hoc/withBasePage.jsx` — тот является оркестратором
 * активной игровой сессии.
 */

import React from 'react';
import styles from './withBaseMainPage.module.css';

const withBaseMainPage = (WrappedComponent) => {
  const WithBaseMainPage = (props) => {
    return (
      <div className={styles.baseMainPage}>
        <WrappedComponent {...props} />
      </div>
    );
  };

  // Для сохранения имени компонента в отладке
  WithBaseMainPage.displayName = `withBaseMainPage(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return WithBaseMainPage;
};

export default withBaseMainPage;

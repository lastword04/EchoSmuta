import { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { checkUnreadMail } from '../../../entities/mail/store/mailSlice';
import { 
  useGetInboxQuery, 
  useGetSentQuery, 
  useDeleteInboxMailMutation, 
  useDeleteSentMailMutation
} from '../../../entities/mail/api/mailApi';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from './MailModal.module.css';
import btn from '../../../shared/styles/buttons.module.css';

export const MailModal = ({ onClose, onOpenFriends }) => {
  const [activeTab, setActiveTab] = useState('inbox');
  const [page, setPage] = useState(1);
  const [deletingIds, setDeletingIds] = useState(new Set());
  const dispatch = useDispatch();

  const limit = 10;
  const offset = (page - 1) * limit;
  

  // RTK Query: оба query активны, keepPreviousData для плавной пагинации
  const { 
    data: inboxData, 
    isLoading: isInboxLoading,
    isFetching: isInboxFetching,
  } = useGetInboxQuery({ limit, offset }, { keepPreviousData: true });

  const { 
    data: sentData, 
    isLoading: isSentLoading,
    isFetching: isSentFetching,
  } = useGetSentQuery({ limit, offset }, { keepPreviousData: true });

  const [deleteInboxMail] = useDeleteInboxMailMutation();
  const [deleteSentMail] = useDeleteSentMailMutation();

  useEffect(() => {
    if (activeTab === 'inbox' && inboxData !== undefined && !isInboxFetching) {
      dispatch(checkUnreadMail());
    }
  }, [activeTab, inboxData, isInboxFetching, dispatch]);

  const messages = activeTab === 'inbox' 
    ? (inboxData?.objects || []) 
    : (sentData?.objects || []);
  const count = activeTab === 'inbox' 
    ? (inboxData?.count || 0) 
    : (sentData?.count || 0);
  const isLoading = activeTab === 'inbox' ? isInboxLoading : isSentLoading;
  const isFetching = activeTab === 'inbox' ? isInboxFetching : isSentFetching;

  const handleDelete = async (mailId) => {
    if (deletingIds.has(mailId) || isLoading) return;

    setDeletingIds(prev => new Set([...prev, mailId]));
    try {
      if (activeTab === 'inbox') {
        await deleteInboxMail(mailId).unwrap();
        dispatch(checkUnreadMail());
      } else {
        await deleteSentMail(mailId).unwrap();
      }
    } catch (error) {
      console.error('Ошибка при удалении письма:', error);
    } finally {
      setDeletingIds(prev => {
        const next = new Set(prev);
        next.delete(mailId);
        return next;
      });
    }
  };

  const handleTabClick = (newTab) => {
    if (isLoading) return;

    if (newTab === activeTab) {
      if (activeTab === 'inbox') {
        dispatch(checkUnreadMail());
      }
      return;
    }

    setPage(1);
    setActiveTab(newTab);
  };

  const totalPages = Math.max(1, Math.ceil(count / limit));

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Вкладки */}
        <div className={styles.header}>
          <div className={styles.tabsAndCloseButton}>
            <div className={btn.tabGroup}>
              <button
                className={`${btn.textTab} ${activeTab === 'inbox' ? btn.textTabActive : ''}`}
                onClick={() => handleTabClick('inbox')}
                disabled={isLoading}
              >
                Входящие
              </button>
              <span className={styles.dot}>•</span>          
              <button
                className={`${btn.textTab} ${activeTab === 'sent' ? btn.textTabActive : ''}`}
                onClick={() => handleTabClick('sent')}
                disabled={isLoading}
              >
                Отправленные
              </button>
              <span className={styles.dot}>•</span>
              <button
                className={btn.textTab}
                onClick={() => {
                  if (onOpenFriends) onOpenFriends();
                }}
              >
                Написать письмо
              </button>              
            </div>
            {/* Закрыть */}
              <button className={styles.closeButton} onClick={onClose}>
                ✕
              </button>
          </div>
        </div>

        {/* Контент - показываем "Нет сообщений" только когда данных реально нет */}
        {messages.length === 0 && !isFetching ? (
          <div className={styles.empty}>Нет сообщений</div>
        ) : messages.length > 0 ? (
          <div className={styles.messagesList}>
            {messages.map((msg) => (
              <div key={msg.id} className={styles.messageCard}>
                <div className={styles.messageHeader}>
                  <span className={styles.messageDate}>
                    {parseUtcDate(msg.created_at).toLocaleString('ru-RU', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false
                    }).replace(',', '')}
                  </span>
                  <span className={styles.middleDot}>•</span>
                  {activeTab === 'inbox' ? (
                    msg.sender_status === 'user' ? (
                      <a
                        href="#"
                        className={styles.characterSender}
                        onClick={(e) => {
                          e.preventDefault();
                          window.open(`/characters/${msg.from_character_id}`, '_blank');
                        }}
                      >
                        {msg.from_character_name}
                      </a>
                    ) : (
                      <span className={styles.systemMessage}>Системное сообщение</span>
                    )
                  ) : (
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        window.open(`/characters/${msg.to_character_id}`, '_blank');
                      }}
                    >
                      {msg.to_character_name}
                    </a>
                  )}
                  <button 
                    className={styles.deleteButton} 
                    onClick={() => handleDelete(msg.id)}
                    disabled={deletingIds.has(msg.id) || isLoading}
                  >
                    ✕
                  </button>
                </div>
                <div className={styles.messageBody}>{msg.message}</div>
              </div>
            ))}
          </div>
        ) : null}

        {/* Пагинация */}
        <div className={styles.pagination}>
          <button
            disabled={page <= 1 || isLoading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            {'<'}
          </button>
          <span className={`${styles.pageNumber} ${totalPages === 1 ? styles.pageDisabled : ''}`}>
            {page}
          </span>
          <button
            disabled={page >= totalPages || isLoading}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            {'>'}
          </button>
        </div>
        
      </div>
    </div>
  );
};
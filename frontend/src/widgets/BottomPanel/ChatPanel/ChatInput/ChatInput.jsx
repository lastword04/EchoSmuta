import { useEffect, useState, useRef } from 'react';
import { transliterate } from '../../../../shared/lib/utils/translit';
import { useLazyGetSimpleCharacterByNameQuery } from '../../../../entities/character/api/characterApi';
import styles from './ChatInput.module.css';

const ChatInput = ({ 
  settings, 
  onSettingsToggle, 
  onSendMessage, 
  selectedCharacters, 
  isTradeMode, 
  onTradeToggle, 
  onClearChat, 
  onShowBells,
  setInputValue,
  inputValue
}) => {
  const {
    chat_enabled,
    show_journal,
    show_bell,
    show_translit,
    show_lastic,
    show_clear_screen,
    show_trade_messages_button,
  } = settings;

  const [journalOpen, setJournalOpen] = useState(false);
  const [recipient, setRecipient] = useState('');
  const [recipientError, setRecipientError] = useState('');  

  const journalRef = useRef(null);
  const journalButtonRef = useRef(null);

  // trigger - это функция, которую мы вызовем по клику. isSearching - флаг загрузки.
  const [triggerGetSimpleCharacter, { isFetching: isSearching }] = useLazyGetSimpleCharacterByNameQuery();

  // 🔹 эффект для отслеживания клика вне блока журнала
  useEffect(() => {
    if (!journalOpen) return;

    const handleClickOutside = (e) => {
      if (
        journalRef.current &&
        !journalRef.current.contains(e.target) &&
        journalButtonRef.current &&
        !journalButtonRef.current.contains(e.target)
      ) {
        setJournalOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [journalOpen]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleClear = () => {
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTranslitClick = () => {
    if (inputValue.trim()) {
      const translated = transliterate(inputValue);
      setInputValue(translated);
    }
  };

  const handleRecipientKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleRecipientSubmit();
    }
  };

  const handleRecipientSubmit = async () => {
    if (!recipient.trim()) return;

    setRecipientError(''); // Сбрасываем старую ошибку

    try {
      // unwrap() заставит блок catch сработать, если сервер вернет 404 или 500
      const characterData = await triggerGetSimpleCharacter(recipient.trim()).unwrap();
      
      const character = {
        name: characterData.name,
        id: characterData.id,
        isPrivate: true 
      };

      window.dispatchEvent(new CustomEvent('characterSelected', {
        detail: { name: character.name, id: character.id, isPrivate: true }
      }));

      setRecipient('');
      setJournalOpen(false);
    } catch (error) {
      // В RTK Query статус лежит в error.status
      if (error.status === 404) {
        setRecipientError('Персонаж с таким ником не зарегистрирован');
      } else {
        setRecipientError('Ошибка при поиске пользователя');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.chatInputContainer}>
      {show_journal && (
        <div className={styles.iconButton} ref={journalButtonRef} title="Журнал" onClick={() => setJournalOpen(!journalOpen)}>
          <button type="button">
            <img src="/images/widgets/chat-panel/buttons/journal.png" alt="Журнал" />
          </button>
        </div>
      )}

      {journalOpen && (
        <div ref={journalRef} className={styles.journalPanel}>
          <div className={styles.journalButtons}>
            <button type="button" className={styles.journalButton} title="Клан">
              Клан
            </button>
            <button type="button" className={styles.journalButton} title="Соратники">
              Соратники
            </button>
            <button type="button" className={styles.journalButton} title="Противники">
              Противники
            </button>
            <button type="button" className={styles.journalButton} title="ОСИ">
              ОСИ
            </button>
          </div>

          <div className={styles.recipientInputContainer}>
            <input
              type="text"
              placeholder="Адресат"
              className={styles.recipientInput}
              value={recipient}
              maxLength={21}
              onChange={(e) => {
                setRecipient(e.target.value);
                if (recipientError) setRecipientError('');
              }}
              onKeyDown={handleRecipientKeyDown}
            />
            <button
              type="button"
              className={styles.checkButton}
              title="Отправить"
              onClick={handleRecipientSubmit}
              disabled={isSearching}
            >
              ✓
            </button>
          </div>
          
          {recipientError && (
            <div className={styles.recipientError}>
              {recipientError}
            </div>
          )}
        </div>
      )}

      <input
        type="text"
        placeholder={!chat_enabled
          ? "Чат ОФФ!"
          : (selectedCharacters.length > 0
            ? "Введите сообщение для выбранных персонажей..."
            : (isTradeMode ? "Введите торговое сообщение..." : "Введите сообщение..."))
        }
        className={styles.chatInput}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={!chat_enabled}
        maxLength={800}
        title={!chat_enabled ? "Чат отключён" : undefined}
      />

      <div className={styles.iconButton} onClick={handleSubmit} title="Отправить">
        <button type="button">
          <img src="/images/widgets/chat-panel/buttons/send.png" alt="Отправить" />
        </button>
      </div>

      {show_bell && (
        <div className={styles.iconButton} onClick={onShowBells} title="Колобки">
          <button type="button">
            <img src="/images/widgets/chat-panel/buttons/smile.png" alt="Колобки" />
          </button>
        </div>
      )}

      {show_translit && (
        <div className={styles.iconButton} onClick={handleTranslitClick} title="Транслит">
          <button type="button">
            <img src="/images/widgets/chat-panel/buttons/translit.png" alt="Транслит" />
          </button>
        </div>
      )}

      {show_lastic && (
        <div className={styles.iconButton} onClick={handleClear} title="Ластик">
          <button type="button">
            <img src="/images/widgets/chat-panel/buttons/eraser.png" alt="Ластик" />
          </button>
        </div>
      )}

      {show_clear_screen && (
        <div className={styles.iconButton} onClick={onClearChat} title="Очистить окно чата">
          <button type="button">
            <img src="/images/widgets/chat-panel/buttons/clear.png" alt="Очистить окно чата" />
          </button>
        </div>
      )}

      {show_trade_messages_button && (
        <div
          className={`${styles.iconButton} ${isTradeMode ? styles.tradeActive : ''} ${selectedCharacters.length > 0 ? styles.tradeDisabled : ''}`}
          onClick={() => onTradeToggle(!isTradeMode)}
          title={selectedCharacters.length > 0 ? 'Торговля недоступна при выборе адресата' : (isTradeMode ? 'Отключить торговлю' : 'Включить торговлю')}
        >
          <button type="button">
            <img
              src="/images/widgets/chat-panel/buttons/trade.png"
              alt="Торговля"
              className={isTradeMode ? styles.tradeActiveIcon : ''}
            />
          </button>
        </div>
      )}


      <div className={styles.iconButton} onClick={onSettingsToggle} title="Настройки">
        <button type="button">
          <img src="/images/widgets/chat-panel/buttons/settings.png" alt="Настройки" />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
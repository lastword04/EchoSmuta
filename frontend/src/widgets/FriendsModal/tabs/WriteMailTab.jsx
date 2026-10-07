import React, { useState, useEffect } from "react";
import { useDispatch } from 'react-redux';
import { 
  useGetMailSettingsQuery,
  useSendMailMutation,
  useBlockSendMessageMutation,
  useUnblockSendMessageMutation
} from "../../../entities/mail/api/mailApi";
import { checkUnreadMail } from "../../../entities/mail/store/mailSlice";
import styles from "../FriendsModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const WriteMailTab = ({ doNotReceive, setDoNotReceive }) => {
  const dispatch = useDispatch();
  const [recipient, setRecipient] = useState("");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isBlockToggleLoading, setIsBlockToggleLoading] = useState(false);
  const [blockError, setBlockError] = useState("");

  const maxRecipientLength = 21;
  const maxMessageLength = 1000;

  // RTK Query: автоматическая загрузка настроек блокировки
  const { data: mailSettings } = useGetMailSettingsQuery();

  // Синхронизация doNotReceive из RTK Query кэша
  useEffect(() => {
    if (mailSettings !== undefined) {
      setDoNotReceive(!!mailSettings?.is_block_send_mails);
    }
  }, [mailSettings, setDoNotReceive]);

  // RTK Query мутации
  const [sendMail] = useSendMailMutation();
  const [blockSendMessage] = useBlockSendMessageMutation();
  const [unblockSendMessage] = useUnblockSendMessageMutation();

  const handleSend = async () => {
    setErrorMessage("");
    setSuccessMessage("");

    if (!recipient.trim()) return setErrorMessage("Введите ник персонажа");
    if (!message.trim()) return setErrorMessage("Введите текст письма");

    setIsSending(true);
    try {
      await sendMail({
        to_character_name: recipient.trim(),
        message: message.trim(),
      }).unwrap();
      
      setSuccessMessage("Отправлено");
      setRecipient("");
      setMessage("");
      
      // Инвалидация тега 'Mail' обновит входящие у получателя
      // Обновляем счётчик непрочитанных (на случай если письмо системное)
      dispatch(checkUnreadMail());
    } catch (error) {
      console.error("Ошибка отправки письма:", error);
      if (error.status === 404) {
        setErrorMessage("Персонажа с таким ником не существует");
      } else if (error.status === 400) {
        if (error.data?.error_code === "CANNOT_SEND_MESSAGE_TO_CHARACTER") {
          setErrorMessage("Персонаж запретил отправлять ему ПМ");
        } else if (error.data?.error_code === "CANNOT_SEND_MESSAGE_TO_SELF") {
          setErrorMessage("Нельзя отправить письмо самому себе");
        } else {
          setErrorMessage("Ошибка при отправке письма");
        }
      } else {
        setErrorMessage("Ошибка при отправке письма");
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleBlockToggle = async (e) => {
    const isChecked = e.target.checked;
    setIsBlockToggleLoading(true);
    setBlockError("");

    try {
      if (isChecked) {
        await blockSendMessage().unwrap();
      } else {
        await unblockSendMessage().unwrap();
      }
      setDoNotReceive(isChecked);
      // Инвалидация тега 'MailSettings' автоматически рефетчит useGetMailSettingsQuery
    } catch (err) {
      console.error("Ошибка изменения блокировки:", err);
      setBlockError(isChecked 
        ? "Не удалось заблокировать получение писем" 
        : "Не удалось разблокировать получение писем"
      );
    } finally {
      setIsBlockToggleLoading(false);
    }
  };

  // Если данные о блокировке ещё не подгружены — показываем заглушку
  if (doNotReceive === null || doNotReceive === undefined) return <div>Загрузка...</div>;

  return (
    <div className={styles.writeMail}>
      <label className={styles.checkboxLabelTop}>
        <input
          type="checkbox"
          checked={doNotReceive}
          onChange={handleBlockToggle}
          disabled={isBlockToggleLoading}
        />
        Не получать письма
      </label>
      {blockError && (
        <span className={styles.errorText}>{blockError}</span>
      )}
      <label className={styles.recipientLabel}>
        Адресат:
        <input
          type="text"
          value={recipient}
          onChange={(e) => {
            if (e.target.value.length <= maxRecipientLength)
              setRecipient(e.target.value);
          }}
          placeholder="Ник"
          className={styles.recipientInput}
        />
      </label>

      {errorMessage && (
        <span className={styles.errorText}>{errorMessage}</span>
      )}

      <div className={styles.textareaWrapper}>
        <textarea
          className={styles.messageArea}
          value={message}
          onChange={(e) => {
            if (e.target.value.length <= maxMessageLength)
              setMessage(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") e.preventDefault();
          }}
          onPaste={(e) => {
            e.preventDefault();
            const pastedText = e.clipboardData.getData('text/plain').replace(/\n/g, '');
            const newValue = message + pastedText;
            setMessage(newValue.slice(0, maxMessageLength));
          }}
          placeholder="Введите текст письма..."
        />
        <span className={styles.counter}>
          {message.length} / {maxMessageLength}
        </span>
      </div>

      <div className={styles.footer}>
        <div className={styles.actions}>
          {successMessage && (
            <span className={styles.successTextLeft}>{successMessage}</span>
          )}
          <button
            className={btn.accentButton}
            onClick={handleSend}
            disabled={isSending}
          >
            {isSending ? "Отправка..." : "Отправить"}
          </button>
        </div>
      </div>
    </div>
  );
};
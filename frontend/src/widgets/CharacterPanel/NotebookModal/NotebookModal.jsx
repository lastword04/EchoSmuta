import React, { useState, useEffect } from "react";
import { 
  useGetMyNotebookQuery, 
  useUpdateNotebookMutation 
} from "../../../entities/character/api/notebookApi"; // Проверь путь!
import styles from "./NotebookModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const NotebookModal = ({ onClose }) => {
  const [text, setText] = useState("");
  const [saveMessage, setSaveMessage] = useState("");
  const maxLength = 5000;

  // 1. Загружаем данные через RTK Query
  const { data: notebookData } = useGetMyNotebookQuery();
  
  // 2. Готовим мутацию для сохранения
  const [updateNotebook, { isLoading: isSaving }] = useUpdateNotebookMutation();

  // 3. Синхронизируем локальный стейт textarea с данными из кэша при первой загрузке
  useEffect(() => {
    if (notebookData) {
      setText(notebookData.text || "");
    }
  }, [notebookData]);

  const handleChange = (e) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setText(value);
    }
  };

  const handleSave = async () => {
    if (!notebookData) {
      setSaveMessage("Нет данных блокнота для сохранения");
      return;
    }

    setSaveMessage(""); // Очищаем предыдущие сообщения

    try {
      await updateNotebook({ 
        notebookId: notebookData.id, 
        data: { text } 
      }).unwrap();
      
      setSaveMessage("Успешно сохранено");
      
      // Автоматически скрываем сообщение об успехе через 3 секунды
      setTimeout(() => setSaveMessage(""), 3000);
    } catch (error) {
      console.error('Ошибка сохранения блокнота:', error);
      setSaveMessage("Ошибка сохранения");
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Блокнот</h2>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>

        <textarea
          className={styles.textarea}
          value={text}
          onChange={handleChange}
          maxLength={maxLength}
          disabled={!notebookData || isSaving}
        />

        <div className={styles.footer}>
          <div className={styles.leftSection}>
            <span className={styles.counter}>
              {text.length} / {maxLength}
            </span>
            {saveMessage && (
              <span 
                className={`${styles.saveMessage} ${
                  saveMessage.includes('Ошибка') ? styles.error : styles.success
                }`}
              >
                {saveMessage}
              </span>
            )}
          </div>
          <button 
            className={btn.accentButton} 
            onClick={handleSave}
            disabled={isSaving || !notebookData} // Защита от спама
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
};
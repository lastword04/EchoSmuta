import React, { useState, useEffect } from "react";
import { 
  useGetMyInfoQuery, 
  useUpdateMyInfoMutation 
} from "../../../entities/character/api/characterApi";
import styles from "./CharacterInfoModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const CharacterInfoModal = ({ onClose }) => {
  const [formData, setFormData] = useState({
    name: "",
    country: "",
    city: "",
    information: ""
  });
  const [saveMessage, setSaveMessage] = useState("");
  const [errors, setErrors] = useState({});

  // 1. Читаем данные из кэша RTK Query
  const { data: myInfoData, isLoading: isFetching } = useGetMyInfoQuery();
  
  // 2. Готовим мутацию
  const [updateMyInfo, { isLoading: isSaving }] = useUpdateMyInfoMutation();

  // 3. Синхронизируем форму, когда данные пришли
  useEffect(() => {
    if (myInfoData) {
      setFormData({
        name: myInfoData.name || "",
        country: myInfoData.country || "",
        city: myInfoData.city || "",
        information: myInfoData.info || "" // Бэкенд возвращает 'info', в стейте 'information'
      });
    }
  }, [myInfoData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSave = async () => {
    if (!myInfoData?.id) return;
    
    setErrors({});
    setSaveMessage("");

    const infoData = {
      name: formData.name || null,
      country: formData.country || null,
      city: formData.city || null,
      info: formData.information || null
    };

    try {
      await updateMyInfo({ infoId: myInfoData.id, infoData }).unwrap();
      setSaveMessage("Информация успешно сохранена");
      setTimeout(() => setSaveMessage(""), 3000);
    } catch (err) {
      // В RTK Query + Axios ошибка лежит в err.data
      const errData = err.data;
      
      if (errData?.error_type === "RequestValidationError" && errData?.extras?.errors) {
        const validationErrors = {};
        errData.extras.errors.forEach(e => {
          const field = e.location?.split(' -> ')[1];
          if (field) validationErrors[field] = e.message;
        });
        setErrors(validationErrors);
        setSaveMessage("Пожалуйста, исправьте ошибки в формах");
      } else {
        setSaveMessage("Ошибка сохранения");
      }
    }
  };

  // Блокируем всё, пока идет первичная загрузка или сохранение
  const isDisabled = isFetching || isSaving;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Информация</h2>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>

        <div className={styles.disclaimer}>
          Данная информация является необязательной, публикация только по собственному желанию.
        </div>

        <div className={styles.form}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Имя</label>
            <input
              type="text" name="name" value={formData.name} onChange={handleChange}
              className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
              disabled={isDisabled} maxLength={25}
            />
            <div className={styles.counter}>{formData.name.length} / 25</div>
            {errors.name && <div className={styles.errorMessage}>{errors.name}</div>}
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Страна</label>
            <input
              type="text" name="country" value={formData.country} onChange={handleChange}
              className={`${styles.input} ${errors.country ? styles.inputError : ''}`}
              disabled={isDisabled} maxLength={25}
            />
            <div className={styles.counter}>{formData.country.length} / 25</div>
            {errors.country && <div className={styles.errorMessage}>{errors.country}</div>}
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Город</label>
            <input
              type="text" name="city" value={formData.city} onChange={handleChange}
              className={`${styles.input} ${errors.city ? styles.inputError : ''}`}
              disabled={isDisabled} maxLength={25}
            />
            <div className={styles.counter}>{formData.city.length} / 25</div>
            {errors.city && <div className={styles.errorMessage}>{errors.city}</div>}
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Информация</label>
            <textarea
              name="information" value={formData.information} onChange={handleChange}
              className={`${styles.textarea} ${errors.information ? styles.inputError : ''}`}
              rows={6} disabled={isDisabled} maxLength={5000}
            />
            <div className={styles.counter}>{formData.information.length} / 5000</div>
            {errors.information && <div className={styles.errorMessage}>{errors.information}</div>}
          </div>
        </div>

        <div className={styles.footer}>
          <div className={styles.leftSection}>
            {saveMessage && (
              <span className={`${styles.saveMessage} ${saveMessage.includes('Ошибка') || saveMessage.includes('исправьте') ? styles.error : styles.success}`}>
                {saveMessage}
              </span>
            )}
          </div>
          <button 
            className={btn.accentButton} 
            onClick={handleSave}
            disabled={isDisabled}
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );
};
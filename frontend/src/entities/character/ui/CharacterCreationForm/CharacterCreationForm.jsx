// src/features/character/ui/CharacterCreationForm/CharacterCreationForm.jsx
import { useState } from 'react';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { Input } from '../../../../shared/ui/Input/Input';
import { Select } from '../../../../shared/ui/Select/Select';
import { config } from '../../../../shared/config/env/env';
import { generateTemplateName } from '../../../file/api/fileApi';
import { useCreateCharacterMutation, characterApi } from '../../api/characterApi';
import { useDispatch } from 'react-redux';
import { races, genders, raceDescriptions } from '../../../../shared/config/character/characterData';
import styles from './CharacterCreationForm.module.css';

export const CharacterCreationForm = ({ onSuccess, onCancel }) => {
  const dispatch = useDispatch();
  const [createCharacter, { isLoading }] = useCreateCharacterMutation();

  const [formData, setFormData] = useState({
    characterName: '',
    race: '',
    gender: ''
  });
  
  const [errors, setErrors] = useState({});  
  const templateName = formData.race && formData.gender
    ? generateTemplateName(formData.race, formData.gender)
    : null;
  const characterImage = templateName
    ? `${config.FILE_API_BASE_URL}/template_name/${templateName}/content`
    : null;

  

  const clearError = (fieldName) => {
    if (errors[fieldName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    clearError(name);
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    clearError(name);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.characterName.trim()) {
      newErrors.characterName = 'Введите имя персонажа';
    } else if (formData.characterName.length < 2) {
      newErrors.characterName = 'Имя персонажа не должно быть меньше 2 символов';
    } else if (formData.characterName.length > 21) {
      newErrors.characterName = 'Имя персонажа не должно превышать 21 символ';
    } else {
      if (!/^[a-zA-Zа-яА-ЯёЁ0-9\s]+$/.test(formData.characterName)) {
        newErrors.characterName = 'Имя может содержать только буквы, цифры и пробелы';
      } else if (/[a-zA-Z]/.test(formData.characterName) && /[а-яА-ЯёЁ]/.test(formData.characterName)) {
        newErrors.characterName = 'Имя должно содержать буквы только одного языка (русские или латинские)';
      } else if (!formData.characterName.trim()) {
        newErrors.characterName = 'Имя персонажа не может состоять только из пробелов';
      }
    }
    
    if (!formData.race) {
      newErrors.race = 'Выберите расу';
    }
    
    if (!formData.gender) {
      newErrors.gender = 'Выберите пол';
    }
    
    return newErrors;
  };

    const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setErrors({});
    
    try {
      const characterData = {
        name: formData.characterName,
        race: formData.race,
        is_male: formData.gender === 'male'
      };
      
      await createCharacter(characterData).unwrap();
      
      // Принудительно обновляем кэш, чтобы на CharactersPage сразу был новый персонаж
      dispatch(characterApi.util.invalidateTags(['MyCharacters', 'CreationStatus']));
      
      onSuccess?.();
      
    } catch (error) {
      console.error('Character creation error:', error);
      
      if (error?.data) {
        const { extras } = error.data;
        
        if (error.status === 409) {
          if (extras?.field === 'name') {
            setErrors({
              characterName: 'Персонаж с таким именем уже существует'
            });
          } else {
            setErrors({
              general: 'Персонаж с такими данными уже существует'
            });
          }
        } else {
          setErrors({
            general: 'Ошибка создания персонажа. Попробуйте позже.'
          });
        }
      } else {
        setErrors({
          general: 'Ошибка подключения к серверу. Попробуйте позже.'
        });
      }
    }
  };

  return (
    <Card className={styles.creationCard}>
      <div className={styles.header}>
        <h2 className={styles.title}>Создание нового персонажа</h2>
        <p className={styles.subtitle}>Выберите параметры вашего персонажа</p>
      </div>

      {errors.general && (
        <div className={styles.generalError}>
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formSection}>
          <div className={styles.inputWrapper}>
            <Input
              label="Имя персонажа"
              type="text"
              name="characterName"
              placeholder="Только русские или латинские буквы, цифры, максимум 21 символ"
              value={formData.characterName}
              onChange={(e) => {
                if (e.target.value.length <= 21) {
                  handleInputChange(e);
                }
              }}
              error={errors.characterName}
            />
            <div className={styles.charCounter}>
              {formData.characterName.length} / 21
            </div>
          </div>


          <Select
            label="Раса"
            name="race"
            options={races}
            value={formData.race}
            onChange={handleSelectChange}
            error={errors.race}
          />

          {formData.race && raceDescriptions[formData.race] && (
            <div className={styles.raceDescription}>
              <h4 className={styles.raceTitle}>
                {races.find(r => r.value === formData.race)?.label}
              </h4>
              <p className={styles.raceText}>
                {raceDescriptions[formData.race]}
              </p>
            </div>
          )}

          <Select
            label="Пол"
            name="gender"
            options={genders}
            value={formData.gender}
            onChange={handleSelectChange}
            error={errors.gender}
          />
          
          {/* Отображение изображения персонажа */}
          {(formData.race && formData.gender) && (
            <div className={styles.characterPreview}>
              <h4 className={styles.previewTitle}>Предварительный просмотр</h4>
                <img 
                  src={characterImage}
                  alt={`${races.find(r => r.value === formData.race)?.label} ${genders.find(g => g.value === formData.gender)?.label}`}
                  className={styles.characterImage}
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = '/images/city-trade/no-image.png';
                  }}
                />
            </div>
          )}

        </div>

        <div className={styles.actions}>
          <Button
            type="button"
            variant="secondary"
            size="medium"
            onClick={onCancel}
            disabled={isLoading}
            className={styles.cancelButton}
          >
            Отмена
          </Button>
          
          <Button
            type="submit"
            variant="primary"
            size="medium"
            disabled={isLoading}
            className={styles.submitButton}
          >
            Создать персонажа
          </Button>
        </div>
      </form>
    </Card>
  );
};
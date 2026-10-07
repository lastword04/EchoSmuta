import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { Input } from '../../../../shared/ui/Input/Input';
import { Select } from '../../../../shared/ui/Select/Select';
import { 
  useTransferCurrencyMutation,
  characterApi
} from '../../api/characterApi';
import { CharacterTransferItem } from './CharacterTransferItem';
import styles from './CharacterTransferForm.module.css';
import { decimalInputHandler } from '../../../../shared/lib/validation/numberInput';

export const CharacterTransferForm = ({ onSuccess, onCancel, characters, transferRules }) => {
  const dispatch = useDispatch();
  
  const [transferCurrency, { isLoading: isProcessing }] = useTransferCurrencyMutation();
  
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [formData, setFormData] = useState({
    fromCharacterId: '',
    toCharacterId: '',
    ducats: '',
    gold: ''
  });
  const [formErrors, setFormErrors] = useState({});

  const getCharacterById = (id) => {
    return characters.find(char => char.id === id);
  };

  const handleAmountChange = (name) => (e) => {
    decimalInputHandler(
      (value) => setFormData(prev => ({ ...prev, [name]: value })),
      7, 2, { strip: true }
    )(e);

    if (formErrors[name] || error || successMessage) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (formErrors[name] || error || successMessage) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
      setError(null);
      setSuccessMessage(null);
    }
    if (name === 'fromCharacterId') {
      if (value === formData.toCharacterId) {
        setFormData(prev => ({ ...prev, toCharacterId: '' }));
      }
    }
  };

  const validateForm = () => {
    const errors = {};
    if (!formData.fromCharacterId) {
      errors.fromCharacterId = 'Выберите отправителя';
    }
    if (!formData.toCharacterId) {
      errors.toCharacterId = 'Выберите получателя';
    }
    if (formData.ducats === '' && formData.gold === '') {
      errors.ducats = 'Введите сумму для перевода';
      errors.gold = 'Введите сумму для перевода';
    }
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setError(null);
    setFormErrors({});
    setSuccessMessage(null);

    try {
      const transferData = {
        from_character_id: formData.fromCharacterId,
        to_character_id: formData.toCharacterId,
        offered_ducats: formData.ducats ? parseFloat(formData.ducats) : 0,
        offered_gold: formData.gold ? parseFloat(formData.gold) : 0
      };

      const result = await transferCurrency(transferData).unwrap();

      if (result.success) {
        const fromCharacter = getCharacterById(formData.fromCharacterId);
        const toCharacter = getCharacterById(formData.toCharacterId);
        
        let message = `${fromCharacter.name} перевёл `;
        const transferredDucats = parseFloat(result.transferred_ducats || 0);
        const transferredGold = parseFloat(result.transferred_gold || 0);
        const taxApplied = parseFloat(result.tax_applied_ducats || 0);
        const totalDucatsCharged = transferredDucats + taxApplied;
        
        let parts = [];
        if (transferredDucats > 0) {
          parts.push(`${transferredDucats.toFixed(2)} дт.`);
        }
        if (transferredGold > 0) {
          parts.push(`${transferredGold.toFixed(2)} злт.`);
        }
        message += parts.join(' и ') + ` персонажу ${toCharacter.name}.`;
        if (taxApplied > 0) {
          message += ` С учётом налога с персонажа списано ${totalDucatsCharged.toFixed(2)} дт. (включая налог в размере ${taxApplied.toFixed(2)} дт.)`;
        }
        setSuccessMessage(message);
        
        setFormData({
          fromCharacterId: '',
          toCharacterId: '',
          ducats: '',
          gold: ''
        });
        
        // Принудительно инвалидируем кэш — обновятся балансы в CharactersPage
        dispatch(characterApi.util.invalidateTags(['MyCharacters']));
        
        if (onSuccess) {
          onSuccess(result);
        }
      }
    } catch (error) {
      console.error('Transfer error:', error);
      if (error?.data) {
        const { error_code, detail, extras } = error.data;
        switch (error_code) {
          case 'INSUFFICIENT_FUNDS':
            if (extras && extras.currency) {
              if (extras.currency === 'ducats') {
                setFormErrors(prev => ({
                  ...prev,
                  ducats: `Недостаточно дукатов. Требуется: ${extras.required_amount}, доступно: ${extras.current_amount}`
                }));
              } else if (extras.currency === 'gold') {
                setFormErrors(prev => ({
                  ...prev,
                  gold: `Недостаточно золота. Требуется: ${extras.required_amount}, доступно: ${extras.current_amount}`
                }));
              } else {
                setError(detail || 'Недостаточно средств для перевода');
              }
            } else {
              setError('Недостаточно средств для перевода');
            }
            break;
          case 'CHARACTER_NOT_FOUND':
            if (extras && extras.field) {
              if (extras.field === 'from_character_id') {
                setFormErrors(prev => ({ ...prev, fromCharacterId: detail || 'Персонаж-отправитель не найден' }));
              } else if (extras.field === 'to_character_id') {
                setFormErrors(prev => ({ ...prev, toCharacterId: detail || 'Персонаж-получатель не найден' }));
              } else {
                setError(detail || 'Персонаж не найден');
              }
            } else {
              setError(detail || 'Персонаж не найден');
            }
            break;
          case 'CHARACTER_LEVEL_TOO_LOW':
            if (extras && extras.field) {
              if (extras.field === 'from_character_id') {
                setFormErrors(prev => ({ ...prev, fromCharacterId: detail || 'Уровень отправителя слишком низкий' }));
              } else if (extras.field === 'to_character_id') {
                setFormErrors(prev => ({ ...prev, toCharacterId: detail || 'Уровень получателя слишком низкий' }));
              } else {
                setError(detail || 'Уровень персонажа слишком низкий');
              }
            } else {
              setError(detail || 'Уровень персонажа слишком низкий');
            }
            break;
          case 'CHARACTER_ONLINE':
            if (extras && extras.field) {
              if (extras.field === 'from_character_id') {
                setFormErrors(prev => ({ ...prev, fromCharacterId: detail || 'Отправитель должен быть в оффлайне' }));
              } else if (extras.field === 'to_character_id') {
                setFormErrors(prev => ({ ...prev, toCharacterId: detail || 'Получатель должен быть в оффлайне' }));
              } else {
                setError(detail || 'Персонаж должен быть в оффлайне');
              }
            } else {
              setError(detail || 'Персонаж должен быть в оффлайне');
            }
            break;
          case 'TRANSFER_TO_SELF':
            setFormErrors(prev => ({ ...prev, toCharacterId: detail || 'Нельзя переводить самому себе' }));
            break;
          case 'AMOUNT_BELOW_MINIMUM':
            if (extras && extras.field && extras.min_value !== undefined) {
              if (extras.field === 'ducats') {
                setFormErrors(prev => ({ ...prev, ducats: `Сумма дукатов меньше минимальной (${extras.min_value})` }));
              } else if (extras.field === 'gold') {
                setFormErrors(prev => ({ ...prev, gold: `Сумма золота меньше минимальной (${extras.min_value})` }));
              } else {
                setError(detail || 'Сумма меньше минимально допустимой');
              }
            } else {
              setError('Сумма меньше минимально допустимой');
            }
            break;
          case 'INVALID_AMOUNT':
            if (extras && extras.field) {
              if (extras.field === 'ducats') {
                setFormErrors(prev => ({ ...prev, ducats: detail || 'Неверная сумма дукатов' }));
              } else if (extras.field === 'gold') {
                setFormErrors(prev => ({ ...prev, gold: detail || 'Неверная сумма золота' }));
              } else {
                setError(detail || 'Неверная сумма');
              }
            } else {
              setError(detail || 'Неверная сумма');
            }
            break;
          default:
            setError(detail || 'Ошибка перевода валюты. Попробуйте позже.');
        }
      } else {
        setError('Ошибка перевода валюты. Попробуйте позже.');
      }
    }
  };

  const fromCharacterOptions = [
    { value: '', label: 'Выберите отправителя' },
    ...characters.map(char => ({
      value: char.id,
      label: `${char.name} [${char.level}]`
    }))
  ];

  const toCharacterOptions = formData.fromCharacterId
    ? [
        { value: '', label: 'Выберите получателя' },
        ...characters
          .filter(char => char.id !== formData.fromCharacterId)
          .map(char => ({
            value: char.id,
            label: `${char.name} [${char.level}]`
          }))
      ]
    : [{ value: '', label: 'Сначала выберите отправителя' }];

  return (
    <Card className={styles.transferCard}>
      <div className={styles.header}>
        <h2 className={styles.title}>Перевод валюты между персонажами</h2>
        <Button
          variant="outline"
          size="small"
          onClick={onCancel}
          className={styles.backButton}
          disabled={isProcessing}
        >
          ← Назад
        </Button>
      </div>

      {error && (
        <div className={styles.errorMessage}>
          {error}
        </div>
      )}

      <div className={styles.content}>
        <div className={styles.infoSection}>
          <h3 className={styles.sectionTitle}>Информация</h3>
          <div className={styles.infoText}>
            <p>Данная услуга позволяет переводить дукаты между вашими персонажами.</p>
            <ul className={styles.rulesList}>
              <li>Оба ваших персонажа должны быть старше <span className={styles.highlight}>{transferRules?.min_transfer_level || 0}-го уровня</span></li>
              <li>Минимальная сумма перевода составляет <span className={styles.highlight}>{transferRules?.min_transfer_ducats || 0}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. или <span className={styles.highlight}>{transferRules?.min_transfer_gold || 0}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</li>
              <li>Налог на перевод дукатов составляет <span className={styles.highlight}>{(transferRules?.transfer_tax_percentage * 100) || 0}%</span> от суммы перевода</li>
            </ul>
          </div>
        </div>

        <div className={styles.transferSection}>
          <div className={styles.charactersList}>
            <h3 className={styles.sectionTitle}>Ваши персонажи</h3>
            <div className={styles.charactersGrid}>
              {characters.map((character) => {
                return (
                  <CharacterTransferItem
                    key={character.id}
                    character={character}
                    isSelected={
                      character.id === formData.fromCharacterId ||
                      character.id === formData.toCharacterId
                    }
                    onSelect={() => {
                      if (!formData.fromCharacterId) {
                        setFormData((prev) => ({ ...prev, fromCharacterId: character.id }));
                      } else if (formData.fromCharacterId && !formData.toCharacterId) {
                        setFormData((prev) => ({ ...prev, toCharacterId: character.id }));
                      } else {
                        setFormData((prev) => ({
                          ...prev,
                          fromCharacterId: character.id,
                          toCharacterId: '',
                        }));
                      }
                    }}
                  />
                );
              })}
            </div>
          </div>

          <div className={styles.transferForm}>
            <h3 className={styles.sectionTitle}>Форма перевода</h3>
            <form onSubmit={handleSubmit} className={styles.form}>
              <div className={styles.formGroup}>
                <Select
                  label="Отправитель"
                  name="fromCharacterId"
                  options={fromCharacterOptions}
                  value={formData.fromCharacterId}
                  onChange={handleSelectChange}
                  error={formErrors.fromCharacterId}
                />
              </div>
              <div className={styles.formGroup}>
                <Select
                  label="Получатель"
                  name="toCharacterId"
                  options={toCharacterOptions}
                  value={formData.toCharacterId}
                  onChange={handleSelectChange}
                  error={formErrors.toCharacterId}
                  disabled={!formData.fromCharacterId}
                />
              </div>
              <div className={styles.amountInputs}>
                <div className={styles.formGroup2}>
                  <Input
                    label={
                      <span>
                        Дукаты <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                      </span>
                    }
                    type="text"
                    name="ducats"
                    placeholder="0.00"
                    value={formData.ducats}
                    onChange={handleAmountChange('ducats')}
                    error={formErrors.ducats}                    
                  />
                </div>
                <div className={styles.formGroup2}>
                  <Input
                    label={
                      <span>
                        Золото <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} />
                      </span>
                    }
                    type="text"
                    name="gold"
                    placeholder="0.00"
                    value={formData.gold}
                    onChange={handleAmountChange('gold')}
                    error={formErrors.gold}                    
                  />
                </div>
              </div>

              {successMessage && (
                <div className={styles.successMessage}>
                  {successMessage}
                </div>
              )}

              <div className={styles.actions}>
                <Button
                  type="button"
                  variant="secondary"
                  size="medium"
                  onClick={onCancel}
                  disabled={isProcessing}
                  className={styles.cancelButton}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="medium"
                  disabled={isProcessing || !formData.fromCharacterId || !formData.toCharacterId || formData.fromCharacterId === formData.toCharacterId}
                  className={styles.transferButton}
                  style={{ opacity: isProcessing ? 0.6 : 1 }}
                >
                  Подтвердить перевод
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Card>
  );
};
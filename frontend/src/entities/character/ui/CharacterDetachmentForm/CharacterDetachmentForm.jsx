import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { useDetachCharacterMutation, characterApi } from '../../api/characterApi';
import { DetachmentCharacterItem } from './DetachmentCharacterItem';
import { setActiveCharacterName } from '../../../../shared/store/activeCharacterNameSlice';
import { setActiveCharacterId } from '../../../../shared/store/activeCharacterIdSlice';
import styles from './CharacterDetachmentForm.module.css';

export const CharacterDetachmentForm = ({ onSuccess, onCancel, characters, maxCharacters, attachmentSettings }) => {
  const dispatch = useDispatch();
  const activeCharacterId = useSelector((state) => state.local.activeCharacterId);

  // Мгновенный рендер: данные придут из кэша или сети, не блокируя UI
  
  const [detachCharacter, { isLoading: isDetaching }] = useDetachCharacterMutation();

  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [confirmDetachment, setConfirmDetachment] = useState(false);
  const [error, setError] = useState(null);

  const handleCharacterSelect = (character) => {
    setSelectedCharacter(character);
    setConfirmDetachment(false);
    setError(null);
  };

  const calculateDetachCost = (character) => {
    if (!attachmentSettings) return 0;
    return attachmentSettings.detach_cost + (character.level * attachmentSettings.detach_cost_per_level);
  };

  const getMainCharacter = () => {
    return characters?.find(char => char.is_main === true);
  };

  const hasSufficientFunds = (character) => {
    const mainCharacter = getMainCharacter();
    if (!mainCharacter || mainCharacter.ducats === undefined) return false;
    
    const cost = calculateDetachCost(character);
    return mainCharacter.ducats >= cost;
  };

  const isCharacterOnline = (character) => {
    return character.is_online === true;
  };

  const handleDetachment = async () => {
    if (!selectedCharacter || !confirmDetachment) return;

    if (isCharacterOnline(selectedCharacter)) {
      setError('Нельзя открепить персонажа, который находится онлайн.');
      return;
    }

    if (!hasSufficientFunds(selectedCharacter)) {
      setError('Недостаточно дукатов для открепления персонажа.');
      return;
    }

    setError(null);

    try {
      // unwrap() позволяет ловить ошибки в try/catch так же, как с обычным promise
      await detachCharacter(selectedCharacter.id).unwrap();    

      // Атомарно готовим кэш для CharactersPage ДО редиректа.
      // React батчит: текущая страница не успеет перерисоваться с этим списком.
      dispatch(characterApi.util.updateQueryData('getMyCharacters', undefined, (draft) => {
        return draft.filter((c) => c.id !== selectedCharacter.id);
      }));
      dispatch(characterApi.util.updateQueryData('getCharacterCreationStatus', undefined, (draft) => {
        draft.current_characters = Math.max(0, (draft.current_characters || 0) - 1);
      }));
      dispatch(characterApi.util.updateQueryData('getDetachedCharacters', undefined, (draft) => {
        draft.push({ ...selectedCharacter, is_main: false });
      }));
      dispatch(characterApi.util.updateQueryData('checkHasDetachedCharacters', undefined, () => true));

      if (selectedCharacter.id === activeCharacterId) {
        const mainCharacter = getMainCharacter();
        if (mainCharacter) {
          dispatch(setActiveCharacterId(mainCharacter.id));
          dispatch(setActiveCharacterName(mainCharacter.name));
        }
      }

      onSuccess?.();
    } catch (err) {
      console.error('Character detachment error:', err);
      if (err?.status === 400) {
        setError('Недостаточно средств для открепления персонажа.');
      } else if (err?.status === 409) {
        setError('Нельзя открепить персонажа, который находится онлайн.');
      } else {
        setError('Ошибка открепления персонажа. Попробуйте позже.');
      }
    }
  };

  const additionalSlots = maxCharacters - 1;
  const mainCharacter = getMainCharacter();
  const mainCharacterBalance = mainCharacter ? mainCharacter.ducats : 0;

  return (
    <Card className={styles.detachmentCard}>
      <div className={styles.header}>
        <h2 className={styles.title}>Открепление персонажа</h2>
        <Button
          variant="outline"
          size="small"
          onClick={onCancel}
          className={styles.backButton}
          disabled={isDetaching}
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
            <p>На данный момент на одном аккаунте можно иметь 1 основной + {additionalSlots} дополнительный слот для мультов. Основной персонаж создаётся при регистрации аккаунта и не подлежит откреплению.</p>
            <p>Вы можете открепить своего мульта, чтобы освободить слот для регистрации нового персонажа. Открепленный персонаж остается за вами, но становится неактивным и не отображается в списке мультов на странице информации персонажа. Тем не менее, вы можете снова прикрепить персонажа, если имеется свободный слот.</p>
            <p>Персонаж должен находиться оффлайн перед процедурой открепления.</p>
            
            {mainCharacter && (
              <div className={styles.balanceInfo}>
                <p><strong>Баланс основного персонажа:</strong> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {mainCharacterBalance} дт.</p>
              </div>
            )}
            
            {attachmentSettings && (
              <div className={styles.costsInfo}>
                <p><strong>Стоимость открепления:</strong> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {attachmentSettings.detach_cost} дт. + уровень × <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {attachmentSettings.detach_cost_per_level} дт.</p>
                <p><strong>Стоимость прикрепления:</strong> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> {attachmentSettings.attach_cost} злт. + уровень × <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> {attachmentSettings.attach_cost_per_level} злт.</p>
              </div>
            )}
          </div>
        </div>

        <div className={styles.charactersSection}>
          <h3 className={styles.sectionTitle}>Ваши активные персонажи</h3>
          
          {characters && characters.length > 0 ? (
            <div className={styles.charactersList}>
              {characters
                .filter(char => !char.is_main)
                .map(character => (
                  <DetachmentCharacterItem
                    key={character.id}
                    character={character}
                    isSelected={selectedCharacter?.id === character.id}
                    isOnline={isCharacterOnline(character)}
                    onSelect={handleCharacterSelect}
                    calculateDetachCost={calculateDetachCost}
                  />
                ))}
            </div>
          ) : (
            <p className={styles.noCharacters}>Нет доступных персонажей для открепления</p>
          )}
        </div>

        {selectedCharacter && (
          <div className={styles.confirmationSection}>
            {isCharacterOnline(selectedCharacter) ? (
              <div className={styles.onlineWarning}>
                <p>Нельзя открепить персонажа, который находится онлайн.</p>
              </div>
            ) : (
              <>
                <div className={styles.confirmationCheckbox}>
                  <input
                    type="checkbox"
                    id="confirmDetachment"
                    checked={confirmDetachment}
                    onChange={(e) => setConfirmDetachment(e.target.checked)}
                    disabled={isDetaching}
                  />
                  <label htmlFor="confirmDetachment">
                    Я действительно хочу открепить персонажа <strong>{selectedCharacter.name}</strong>
                  </label>
                </div>

                <div className={styles.actions}>
                  <Button
                    type="button"
                    variant="secondary"
                    size="medium"
                    onClick={() => {
                      setSelectedCharacter(null);
                      setConfirmDetachment(false);
                    }}
                    disabled={isDetaching}
                    className={styles.cancelButton}
                  >
                    Отмена
                  </Button>
                  
                  <Button
                    type="button"
                    variant="primary"
                    size="medium"
                    onClick={handleDetachment}
                    disabled={!confirmDetachment || isDetaching || !hasSufficientFunds(selectedCharacter)}
                    className={styles.detachButton}                    
                  >
                    Открепить персонажа
                  </Button>
                </div>
                
                {!hasSufficientFunds(selectedCharacter) && (
                  <div className={styles.insufficientFunds}>
                    Недостаточно средств для открепления персонажа
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
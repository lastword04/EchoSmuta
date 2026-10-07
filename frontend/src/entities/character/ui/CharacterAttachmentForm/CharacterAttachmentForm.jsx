import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import {  
  useGetDetachedCharactersQuery,
  useAttachCharacterMutation,
  characterApi
} from '../../api/characterApi';
import { AttachmentCharacterItem } from './AttachmentCharacterItem';
import styles from './CharacterAttachmentForm.module.css';

export const CharacterAttachmentForm = ({ onSuccess, onCancel, characters = [], maxCharacters, attachmentSettings }) => {
  const dispatch = useDispatch();
  
  const { data: detachedCharacters = [] } = useGetDetachedCharactersQuery();
  const [attachCharacter, { isLoading: isAttaching }] = useAttachCharacterMutation();

  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [confirmAttachment, setConfirmAttachment] = useState(false);
  const [error, setError] = useState(null);

  const handleCharacterSelect = (character) => {
    setSelectedCharacter(character);
    setConfirmAttachment(false);
    setError(null);
  };

  const calculateAttachCost = (character) => {
    if (!attachmentSettings) return 0;
    return attachmentSettings.attach_cost + character.level * attachmentSettings.attach_cost_per_level;
  };

  const getMainCharacter = () => {
    return characters.find(char => char.is_main === true);
  };

  const hasSufficientFunds = (character) => {
    const mainCharacter = getMainCharacter();
    if (!mainCharacter || mainCharacter.gold === undefined) return false;
    const cost = calculateAttachCost(character);
    return mainCharacter.gold >= cost;
  };

  const handleAttachment = async () => {
    if (!selectedCharacter || !confirmAttachment) return;

    setError(null);

    try {
      await attachCharacter({ id: selectedCharacter.id, character: selectedCharacter }).unwrap();
      
      
      
      const remaining = detachedCharacters.filter((c) => c.id !== selectedCharacter.id);

      dispatch(characterApi.util.updateQueryData('getMyCharacters', undefined, (draft) => {
        draft.push({ ...selectedCharacter, is_main: false });
      }));
      dispatch(characterApi.util.updateQueryData('getCharacterCreationStatus', undefined, (draft) => {
        draft.current_characters = (draft.current_characters || 0) + 1;
      }));
      dispatch(characterApi.util.updateQueryData('getDetachedCharacters', undefined, (draft) => {
        return draft.filter((c) => c.id !== selectedCharacter.id);
      }));
      dispatch(characterApi.util.updateQueryData('checkHasDetachedCharacters', undefined, () => remaining.length > 0));

      onSuccess?.();
    } catch (err) {
      console.error('Character attachment error:', err);
      if (err?.status === 400) {
        setError('Недостаточно средств для прикрепления персонажа.');
      } else {
        setError('Ошибка прикрепления персонажа. Попробуйте позже.');
      }
    }
  };

  const mainCharacter = getMainCharacter();
  const mainCharacterBalance = mainCharacter ? mainCharacter.gold : 0;
  const availableSlots = maxCharacters - (characters?.length || 0);

  return (
    <Card className={styles.attachmentCard}>
      <div className={styles.header}>
        <h2 className={styles.title}>Прикрепление персонажа</h2>
        <Button
          variant="outline"
          size="small"
          onClick={onCancel}
          className={styles.backButton}
          disabled={isAttaching}
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
            <p>Вы можете прикрепить ранее открепленного персонажа обратно. Для этого необходимо иметь свободный слот и достаточное количество золота.</p>
            <p>Прикрепленный персонаж снова станет активным и появится в списке ваших персонажей.</p>
            
            {mainCharacter && (
              <div className={styles.balanceInfo}>
                <p><strong>Баланс основного персонажа:</strong> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> {mainCharacterBalance} злт.</p>
              </div>
            )}
            
            <div className={styles.slotsInfo}>
              <p><strong>Доступные слоты:</strong> {availableSlots}</p>
            </div>
            
            {attachmentSettings && (
              <div className={styles.costsInfo}>
                 <p><strong>Стоимость открепления:</strong> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {attachmentSettings.detach_cost} дт. + уровень × <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {attachmentSettings.detach_cost_per_level} дт.</p>
                 <p><strong>Стоимость прикрепления:</strong> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> {attachmentSettings.attach_cost} злт. + уровень × <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> {attachmentSettings.attach_cost_per_level} злт.</p>
              </div>
            )}
          </div>
        </div>

        <div className={styles.charactersSection}>
          <h3 className={styles.sectionTitle}>Ваши открепленные персонажи</h3>
          
          {detachedCharacters.length > 0 ? (
            <div className={styles.charactersList}>
              {detachedCharacters.map((character) => (
                <AttachmentCharacterItem
                  key={character.id}
                  character={character}
                  isSelected={selectedCharacter?.id === character.id}
                  onSelect={handleCharacterSelect}
                  calculateAttachCost={calculateAttachCost}
                />
              ))}
            </div>
          ) : (
            <p className={styles.noCharacters}>Нет открепленных персонажей</p>
          )}
        </div>

        {selectedCharacter && (
          <div className={styles.confirmationSection}>
            <div className={styles.confirmationCheckbox}>
              <input
                type="checkbox"
                id="confirmAttachment"
                checked={confirmAttachment}
                onChange={(e) => setConfirmAttachment(e.target.checked)}
                disabled={isAttaching}
              />
              <label htmlFor="confirmAttachment">
                Я действительно хочу прикрепить персонажа <strong>{selectedCharacter.name}</strong>
              </label>
            </div>

            <div className={styles.actions}>
              <Button
                type="button"
                variant="secondary"
                size="medium"
                onClick={() => {
                  setSelectedCharacter(null);
                  setConfirmAttachment(false);
                }}
                disabled={isAttaching}
                className={styles.cancelButton}
              >
                Отмена
              </Button>
              
              <Button
                type="button"
                variant="primary"
                size="medium"
                onClick={handleAttachment}
                disabled={!confirmAttachment || isAttaching || !hasSufficientFunds(selectedCharacter) || availableSlots <= 0}
                className={styles.attachButton}                
              >
                Прикрепить персонажа
              </Button>
            </div>
            
            {(!hasSufficientFunds(selectedCharacter) || availableSlots <= 0) && (
              <div className={styles.insufficientFunds}>
                {!hasSufficientFunds(selectedCharacter) && 'Недостаточно средств для прикрепления персонажа'}
                {availableSlots <= 0 && 'Нет свободных слотов для прикрепления персонажа'}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
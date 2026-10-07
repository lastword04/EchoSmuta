import React from "react";
import {
  getRaceShield,
  getRaceDisplayName,
  getGenderDisplayName,
} from "../../../entities/character/config/race";
import { getLocationNameAndIsResourceLocation } from "../../../shared/config/locations/locations";
import styles from "../FriendsModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

export const FriendsEnemiesTab = ({
  categories,
  selectedCategoryId,
  setSelectedCategoryId,
  showOnlineOnly,
  setShowOnlineOnly,
  characters,
  addName,
  setAddName,
  addCategoryId,
  setAddCategoryId,
  addError,
  successMessage, 
  handleAdd,
  isAdding,
  handleRemove,
  removingCharacterId,
}) => {
  const maxRecipientLength = 21;

  const handleFilterChange = (e) => {
    setSelectedCategoryId(e.target.value);
  };

  const handleOnlineChange = (e) => {
    setShowOnlineOnly(e.target.checked);
  };

  const getTextLocation = (character) => {
    let resultText = "";
    if (!character.is_online) return resultText = "Вне игры";
    else {
      const {locationName, isResourceLocation} = getLocationNameAndIsResourceLocation(character.location_slug);
      const locationDescription = isResourceLocation ? "Окрестности Авалона" : "Авалон";
      resultText = `${locationName}, ${locationDescription}`;
    }
    return `(${resultText})`;
  }

  return (
    <div className={styles.friendsEnemies}>
      {/* Добавление персонажа */}
      <div className={styles.addRow}>
        <input
          type="text"
          placeholder="Ник"
          maxLength={maxRecipientLength}
          className={styles.nickInput}
          value={addName}
          onChange={(e) => setAddName(e.target.value)}
        />
        <select
          className={styles.categorySelect}
          value={addCategoryId}
          onChange={(e) => setAddCategoryId(e.target.value)}
        >
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
        <button
          className={btn.accentButton}
          onClick={handleAdd}
          disabled={!addName.trim() || !addCategoryId || isAdding}
        >
          Добавить
        </button>
      </div>

      {/* Сообщения */}
      {addError && <div className={styles.addError}>{addError}</div>}
      {successMessage && <div className={styles.successText}>{successMessage}</div>}

      {/* Фильтры */}
      <div className={styles.filterRow}>
        <label className={styles.filterLabel}>
          Показать:
          <select
            className={styles.filterSelect}
            value={selectedCategoryId}
            onChange={handleFilterChange}
          >
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.onlineCheckbox}>
          <input
            type="checkbox"
            checked={showOnlineOnly}
            onChange={handleOnlineChange}           
          />
          Только онлайн
          </label>
      </div>

      {/* Список персонажей */}
      <div className={styles.characterList}>
        {characters.length === 0 ? (
          <div className={styles.placeholder}>Нет персонажей</div>
        ) : (
          characters.map((char) => {
            const shieldIcon = getRaceShield(char.race, char.is_male);
            const locationText = getTextLocation(char);
            return (
              <div key={char.id} className={styles.characterRow}>
                <div className={styles.spacer} title="Вне клана"></div> 
                
                <span className={styles.characterInfo}>
                   
                  <span className={styles.characterName}>
                    {char.name}{" "}
                  </span>
                  <span className={styles.characterLevel} 
                  onClick={() => window.open(`/characters/${char.id}`, "_blank")} style={{cursor: "pointer"}}
                  >
                  [{char.level}] </span>
                  {" "}
                  {shieldIcon && (
                    <img
                      src={shieldIcon}
                      alt={`${getRaceDisplayName(char.race)} ${getGenderDisplayName(char.is_male)}`}
                      className={styles.shieldIcon}
                      onClick={() => window.open(`/characters/${char.id}`, "_blank")}
                      style={{ cursor: "pointer" }}
                      onError={(e) => (e.target.style.display = "none")}
                    />
                  )}
                  <span className={styles.characterLocation}>{locationText}</span>
                </span>

                <button
                  className={btn.textLinkDanger}
                  onClick={() => handleRemove(char.id)}  
                  disabled={removingCharacterId === char.id}                
                >
                  ✕
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

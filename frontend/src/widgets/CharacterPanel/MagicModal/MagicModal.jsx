import React, { useState } from "react";
import { ElixirsTab } from "./tabs/ElixirsTab";
import { EffectsTab } from "./tabs/EffectsTab";
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { characterStatsApi } from '../../../entities/character/api/characterStatsApi';
import { useDispatch } from 'react-redux';
import styles from "./MagicModal.module.css";
import btn from '../../../shared/styles/buttons.module.css';

const TAB_INVALIDATE = {
  elixirs: (d) => d(inventoryApi.util.invalidateTags(["Inventory"])),
  effects: (d) => d(characterStatsApi.util.invalidateTags(["Buffs"])),
};

export const MagicModal = ({ onClose, character }) => {
  const [activeTab, setActiveTab] = useState('elixirs');
  const dispatch = useDispatch();

  const switchTab = (tab) => {
    if (activeTab === tab) {
      TAB_INVALIDATE[tab]?.(dispatch);
      return;
    }
    setActiveTab(tab);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.tabsAndCloseButton}>
            <div className={btn.tabGroup}>
              <button
                className={`${btn.textTab} ${activeTab === 'elixirs' ? btn.textTabActive : ''}`}
                onClick={() => switchTab('elixirs')}
              >
                Эликсиры
              </button>
              <span className={styles.dot}>•</span>
              <button
                className={`${btn.textTab} ${activeTab === 'effects' ? btn.textTabActive : ''}`}
                onClick={() => switchTab('effects')}
              >
                Эффекты
              </button>
            </div>
            <button className={styles.closeButton} onClick={onClose}>✕</button>
          </div>
        </div>

        <div className={styles.tabContent}>
          {activeTab === 'elixirs' && <ElixirsTab character={character} />}
          {activeTab === 'effects' && <EffectsTab character={character} />}
        </div>
      </div>
    </div>
  );
};
import { useState, useEffect } from 'react';
import axios from 'axios'; // или ваш путь к axios
import styles from './BellsPanel.module.css';

const BellsPanel = ({ onBellSelect }) => {
  const [activeTab, setActiveTab] = useState('Emotions');
  const [bellLists, setBellLists] = useState({});

  // Названия вкладок и соответствующие папки
  const tabConfig = [
    { key: 'Emotions', name: 'Эмоции' },
    { key: 'Relations', name: 'Отношения' },
    { key: 'Battles', name: 'Боевые' },
    { key: 'Party\'s', name: 'Праздничные' },
    { key: 'Other', name: 'Другие' },
  ];

  useEffect(() => {
    const fetchBellInfo = async () => {
      try {
        const response = await axios.get('/bells-info.json');
        setBellLists(response.data);
      } catch (error) {
        console.error('Ошибка загрузки информации о колобках:', error);
      }
    };

    fetchBellInfo();
  }, []);

  const handleBellClick = (number) => {
    onBellSelect(`|${number}|`);
  };

  const getBellsForTab = (tabKey) => {
    return bellLists[tabKey] || [];
  };

  return (
    <div className={styles.bellsContainer}>
      <div className={styles.bellsContent}>
        {/* Вкладки */}
        <div className={styles.tabs}>
          {tabConfig.map(tab => (
            <button
              key={tab.key}
              className={`${styles.tabButton} ${activeTab === tab.key ? styles.activeTab : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.name}
            </button>
          ))}
        </div>

        {/* Содержимое вкладки */}
        <div className={styles.bellsGrid}>
          {getBellsForTab(activeTab).map(number => (
            <div
              key={number}
              className={styles.bellItem}
              onClick={() => handleBellClick(number)}
            >
              <img
                src={`/images/bells/${activeTab}/${number}.gif`}
                alt={`Bell ${number}`}
                className={styles.bellImage}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BellsPanel;
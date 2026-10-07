import { useState } from 'react';
import { useUpdateMySettingsMutation } from '../../../../entities/chat/api/chatApi';
import { chatApi } from '../../../../entities/chat/api/chatApi';
import styles from './ChatSettings.module.css';

const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

export const ChatSettings = ({ settings, onUpdate, onSettingsReload, dispatch }) => {
  const [localSettings, setLocalSettings] = useState({ ...settings });
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateSettings] = useUpdateMySettingsMutation();

  const handleChange = async (key, value) => {
    const prevValue = localSettings[key];
    const updatedSettings = { ...localSettings, [key]: value };
    setLocalSettings(updatedSettings);

    const { id, created_at, updated_at, ...settingsToSend } = updatedSettings;

    try {
      setIsUpdating(true);
      const response = await updateSettings({ settingsId: id, data: settingsToSend }).unwrap();
      
      // Сразу обновляем RTK Query кэш (не ждём refetch после invalidation)
      dispatch(
        chatApi.util.updateQueryData('getMySettings', undefined, (draft) => {
          Object.assign(draft, response);
        })
      );
      
      onUpdate(response);

      const debouncedReload = debounce(() => {
            if (key === 'chat_enabled') {
                if (prevValue && !value) {
                    onSettingsReload?.('clear');
                } else if (!prevValue && value) {
                    onSettingsReload?.('reload');
                }
            } else if (
                ['filter_only_me_and_my', 'filter_system_messages', 'filter_trade_messages', 'filter_location_messages'].includes(key)
            ) {
                onSettingsReload?.('reload');
            }
        }, 300);

        debouncedReload();

    } catch (error) {
      console.error('Ошибка при сохранении настроек:', error);
    } finally {
      setIsUpdating(false);
    }
  };




  return (
    <div className={styles.settingsContainer}>
      
      <div className={styles.settingsContent}>
        {/* 1. Общие настройки */}
        <div className={styles.settingsGroup}>
          <h4>Общие настройки</h4>
          
          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={!localSettings.chat_enabled}
                onChange={(e) => handleChange('chat_enabled', !e.target.checked)}
                disabled={isUpdating}
              />
              Отключить чат
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.clan_chat_is_blue}
                onChange={(e) => handleChange('clan_chat_is_blue', e.target.checked)}
                disabled={isUpdating}
              />
              Синий цвет клан-чата
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.system_italic}
                onChange={(e) => handleChange('system_italic', e.target.checked)}
                disabled={isUpdating}
              />
              Системные курсивом
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>Шрифт:</label>
            <select
              value={localSettings.font_size}
              onChange={(e) => handleChange('font_size', Number(e.target.value))}
              disabled={isUpdating}
            >
              {[13, 14, 15, 16].map(size => (
                <option key={size} value={size}>{size}px</option>
              ))}
            </select>
          </div>
        </div>

        {/* 2. Фильтр сообщений */}
        <div className={styles.settingsGroup}>
          <h4>Фильтр сообщений</h4>
          
          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.filter_only_me_and_my}
                onChange={(e) => handleChange('filter_only_me_and_my', e.target.checked)}
                disabled={isUpdating}
              />
              Только мне и мои
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.filter_system_messages}
                onChange={(e) => handleChange('filter_system_messages', e.target.checked)}
                disabled={isUpdating}
              />
              Видеть системные
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.filter_trade_messages}
                onChange={(e) => handleChange('filter_trade_messages', e.target.checked)}
                disabled={isUpdating}
              />
              Видеть торговые
            </label>
          </div>
          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.filter_location_messages}
                onChange={(e) => handleChange('filter_location_messages', e.target.checked)}
                disabled={isUpdating}
              />
              Чат локации
            </label>
          </div>
        </div>

        {/* 3. Кнопки чата */}
        <div className={styles.settingsGroup}>
          <h4>Кнопки чата</h4>
          
          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_journal}
                onChange={(e) => handleChange('show_journal', e.target.checked)}
                disabled={isUpdating}
              />
              Журнал
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_bell}
                onChange={(e) => handleChange('show_bell', e.target.checked)}
                disabled={isUpdating}
              />
              Колобки
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_translit}
                onChange={(e) => handleChange('show_translit', e.target.checked)}
                disabled={isUpdating}
              />
              Транслит
            </label>
          </div>

          <div className={styles.settingRow} title='Стереть строку ввода'>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_lastic}
                onChange={(e) => handleChange('show_lastic', e.target.checked)}
                disabled={isUpdating}
               
              />
              Ластик
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_clear_screen}
                onChange={(e) => handleChange('show_clear_screen', e.target.checked)}
                disabled={isUpdating}
              />
              Очистка экрана
            </label>
          </div>

          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.show_trade_messages_button}
                onChange={(e) => handleChange('show_trade_messages_button', e.target.checked)}
                disabled={isUpdating}
              />
              Торговые сообщения
            </label>
          </div>
        </div>

        {/* 4. Звуки */}
        <div className={styles.settingsGroup}>
          <h4>Звуки</h4>
          
          {/* Текст "Сообщения" */}
          <div className={styles.textLabel}>Сообщения</div>
          <div className={styles.settingRow} title='Сообщения, адресованные персонажу в общем чате'>
            <label>
              <input
                type="checkbox"
                checked={localSettings.sound_general_chat}
                onChange={(e) => handleChange('sound_general_chat', e.target.checked)}
                disabled={isUpdating}
              />
              Общий чат
            </label>
          </div>

          <div className={styles.settingRow} title='Приватные сообщения, адресованные персонажу'>
            <label>
              <input
                type="checkbox"
                checked={localSettings.sound_private_message}
                onChange={(e) => handleChange('sound_private_message', e.target.checked)}
                disabled={isUpdating}
              />
              Приватное сообщение
            </label>
          </div>

          <div className={styles.settingRow} title='Клановые сообщения и сообщения Соратники-Противники'>
            <label>
              <input
                type="checkbox"
                checked={localSettings.sound_clan_battle}
                onChange={(e) => handleChange('sound_clan_battle', e.target.checked)}
                disabled={isUpdating}
              />
              Клан, бой
            </label>
          </div>

          {/* Текст "Бой" */}
          <div className={styles.textLabel}>Бой</div>
          <div className={styles.settingRow}>
            <label>
              <input
                type="checkbox"
                checked={localSettings.sound_battle_start}
                onChange={(e) => handleChange('sound_battle_start', e.target.checked)}
                disabled={isUpdating}
              />
              Начало боя
            </label>
          </div>

          <div className={styles.settingRow} title='Звуковое уведомление за 5 секунд до окончания времени для выставления (или нанесения) удара'>
            <label>
              <input
                type="checkbox"
                checked={localSettings.sound_timeout}
                onChange={(e) => handleChange('sound_timeout', e.target.checked)}
                disabled={isUpdating}
              />
              Тайм-аут
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};
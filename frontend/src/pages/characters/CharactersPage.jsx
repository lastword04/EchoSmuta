import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { inventoryApi } from '../../entities/items/api/inventoryApi';
import { characterStatsApi } from '../../entities/character/api/characterStatsApi';
import { economyApi } from '../../entities/economy/api/economyApi';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';

import { CharacterCard } from '../../entities/character/ui/CharacterCard/CharacterCard';
import { currencyApi } from '../../entities/character/api/currencyApi';
import { 
  characterApi,
  useGetMyCharactersQuery, 
  useGetCharacterCreationStatusQuery,
  useCheckHasDetachedCharactersQuery,
  useGetAttachmentSettingsQuery,
  useGetDetachedCharactersQuery,
  useGetTransferRulesQuery,
  useGetReferralLinkQuery,
} from '../../entities/character/api/characterApi';
import { useGetExchangeSettingsQuery } from '../../entities/character/api/currencyApi';
import { useLogoutMutation } from '../../entities/auth/api/authLogoutApi';
import { usePlayMainMutation } from '../../entities/auth/api/authGameApi';
import { CurrencyExchangeForm } from '../../entities/character/ui/CurrencyExchangeForm/CurrencyExchangeForm';
import { ReferralsPage } from '../referrals/ReferralsPage';
import { useMediaQuery } from '../../shared/hooks/ui/useMediaQuery';
import { setActiveCharacterName } from '../../shared/store/activeCharacterNameSlice';
import { setActiveCharacterId, clearActiveCharacterId } from '../../shared/store/activeCharacterIdSlice';
import { clearUserRole } from '../../shared/store/userRoleSlice';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import visitService from '../../shared/services/visitService';
import styles from './CharactersPage.module.css';

const VALID_TABS = ['characters', 'game', 'currency', 'referrals', 'donations', 'play'];

  const CharactersPageComponent = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const dispatch = useDispatch();
  const [playMain] = usePlayMainMutation();
  const [logout] = useLogoutMutation();

  const activeCharacterName = useSelector((state) => state.local.activeCharacterName);

  const tabFromUrl = searchParams.get('tab');
  const activeTab = VALID_TABS.includes(tabFromUrl) ? tabFromUrl : 'characters';

  const { data: characters = [], isLoading: loading, error } = useGetMyCharactersQuery();

  const { data: characterCreationStatus = { can_create: false, current_characters: 0, max_characters: 0 }, isLoading: statusLoading } = useGetCharacterCreationStatusQuery();

  const { data: hasDetachedCharacters = false, isLoading: detachedLoading } = useCheckHasDetachedCharactersQuery();

  // Прогрев кэшей для страниц attach/detach — результат здесь не нужен,
  // нужно чтобы к моменту перехода данные уже лежали в кэше
  useGetAttachmentSettingsQuery();
  useGetDetachedCharactersQuery();
  useGetTransferRulesQuery();
  useGetReferralLinkQuery();
  useGetExchangeSettingsQuery();
  
  const [showCurrencyExchangeForm, setShowCurrencyExchangeForm] = useState(false);    

  // ⬇️ Здесь добавляем media-запрос
  const isMobile = useMediaQuery('(max-width: 480px)');


  // Состояние для отслеживания обновлений вкладок
  const [refreshTrigger, setRefreshTrigger] = useState({});

 

  const handleCurrencyExchangeSuccess = async () => {
    dispatch(characterApi.util.invalidateTags(['MyCharacters', 'CreationStatus', 'DetachedStatus']));
  };

  const handlePlayMain = async () => {
    try {
      const fingerprint = await visitService.getFingerprint();
      const data = {
        fingerprint: fingerprint
      };
      
      const inGameCharacter = await playMain(data).unwrap();
      // Сброс + смена персонажа + navigate в ОДНОМ тике:
      // кабинет не успевает перерисоваться пустым, а /location стартует с чистым кэшем
      dispatch(inventoryApi.util.resetApiState());
      dispatch(characterApi.util.resetApiState());
      dispatch(characterStatsApi.util.resetApiState());
      dispatch(economyApi.util.resetApiState());
      dispatch(setActiveCharacterId(inGameCharacter.id));
      dispatch(setActiveCharacterName(inGameCharacter.name));
      navigate('/location');
    } catch (error) {
      if (error?.status === 401 || error?.status === 403) {
        navigate('/login', {
          state: { authRequired: 'Для входа в игру требуется авторизация' }
        });
        return;
      }
      alert('Ошибка входа в игру');
    }
  };

  const handleLogout = async () => {
    try {
      const fingerprint = await visitService.getFingerprint();
      const data = {
        fingerprint: fingerprint
      }
      await logout(data).unwrap();
      // dispatch(clearActiveCharacterName()); //
      dispatch(clearActiveCharacterId());
      dispatch(clearUserRole());
      // Идём сразу на логин, минуя главную — нет двойной навигации
      navigate('/login', { replace: true });      
    } catch {
      navigate('/login', { replace: true });
    }
  };

  const canShowAttachmentButton = () =>
    characterCreationStatus.current_characters < characterCreationStatus.max_characters &&
    hasDetachedCharacters;

  const canShowTransferCurrencyButton = () => characters.length > 1;

  // Функция для переключения вкладки
  const handleTabClick = (tab) => {
    if (!VALID_TABS.includes(tab)) return;

    if (tab === 'characters') {
      setShowCurrencyExchangeForm(false);
      if (activeTab === 'characters') {
        // Инвалидируем кэш, RTK Query сам обновит данные
        dispatch(characterApi.util.invalidateTags(['MyCharacters', 'CreationStatus', 'DetachedStatus']));
      } else {
        setSearchParams({ tab: 'characters' });
      }
      return;
    }

    // Для остальных вкладок
    if (tab === activeTab) {
      // Повторное нажатие по той же вкладке — обновление:
      // инвалидация тегов заставляет RTK Query сделать refetch,
      // ремонт через key сбрасывает локальное состояние формы
      if (tab === 'currency') {
        dispatch(currencyApi.util.invalidateTags(['ExchangeSettings', 'Lots']));
      } else if (tab === 'referrals') {
        dispatch(characterApi.util.invalidateTags(['ReferralLink']));
      }
      setRefreshTrigger(prev => ({
        ...prev,
        [tab]: (prev[tab] || 0) + 1
      }));
    } else {
      setSearchParams({ tab });
    }
  };

  // Функция для навигации на страницу прикрепления персонажа
  const handleAttachmentClick = () => {
    navigate('/characters/attach');
  };

  // Функция для навигации на страницу открепления персонажа
  const handleDetachmentClick = () => {
    navigate('/characters/detach');
  };

  // Функция для навигации на страницу создания персонажа
  const handleCreationClick = () => {
    navigate('/characters/create');
  };

  // Функция для навигации на страницу перевода валюты
  const handleTransferClick = () => {
    navigate('/characters/transfer');
  };

  // Атомарный показ: кабинет рисуется только когда ВСЕ данные готовы.
  // F5 = небо (boot-фон) → один кадр → полностью готовый кабинет с карточками.
  const booting = loading || statusLoading || detachedLoading;
  if (booting) return null;
  // Ошибка авторизации: не рисуем кабинет ни одного кадра,
  // ждём глобальный редирект на /login
  if (error && (error.status === 401 || error.status === 403)) return null;


  return (
    <div className={styles.page}>
     
      <div className={styles.content}>
        <Card className={styles.personalCabinetHeader}>
          <div className={styles.cabinetTitle}>
            <h1 
              className={styles.cabinetTitleLink}
              onClick={() => handleTabClick('characters')}
            >
              Личный кабинет
            </h1>
            <p className={styles.greeting}>Привет, {activeCharacterName || 'путешественник'}</p>
          </div>

          <div className={styles.cabinetNavigation}>
            <div className={styles.navTabs}>
              <Button
                variant={activeTab === 'play' ? 'primary' : 'outline'}
                size="small"
                onClick={handlePlayMain}
                className={styles.navButton}
              >
                Войти в игру
              </Button>
              <Button
                variant={activeTab === 'characters' ? 'primary' : 'outline'}
                size="small"
                onClick={() => handleTabClick('characters')}
                className={styles.navButton}
              >
                Ваши персонажи
              </Button>
              <Button
                variant={activeTab === 'game' ? 'primary' : 'outline'}
                size="small"
                onClick={() => handleTabClick('game')}
                className={styles.navButton}
              >
                Игровые услуги
              </Button>
              <Button
                variant={activeTab === 'currency' ? 'primary' : 'outline'}
                size="small"
                onClick={() => handleTabClick('currency')}
                className={styles.navButton}
              >
                Биржа валюты
              </Button>
              <Button
                variant={activeTab === 'referrals' ? 'primary' : 'outline'}
                size="small"
                onClick={() => handleTabClick('referrals')}
                className={styles.navButton}
              >
                Рефералы
              </Button>
              <Button
                variant={activeTab === 'donations' ? 'primary' : 'outline'}
                size="small"
                onClick={() => handleTabClick('donations')}
                className={styles.navButton}
              >
                Пожертвования
              </Button>
              <Button
                variant="secondary"
                size="small"
                onClick={() => window.open('/forum', '_blank')}
                className={styles.navButton}
              >
                Форум
              </Button>
              <Button
                variant="outline"
                size="small"
                onClick={handleLogout}
                className={styles.navButton}
              >
                Выход
              </Button>
            </div>
          </div>
        </Card>

        <Card className={styles.charactersCard}>
          {activeTab === 'characters' &&
            !showCurrencyExchangeForm && (
              <>
                <div className={styles.header}>
                  <h2 className={styles.title}>Выбор персонажа</h2>
                    <div className={styles.characterCount}>
                      {loading
                        ? (isMobile ? '(–/–)' : 'Персонажей: –/–')
                        : (isMobile
                          ? `(${characterCreationStatus.current_characters}/${characterCreationStatus.max_characters})`
                          : `Персонажей: ${characterCreationStatus.current_characters}/${characterCreationStatus.max_characters}`)}
                    </div>
                </div>

                {error && (
                  <div className={styles.errorMessage}>
                    {error.status === 401 || error.status === 403
                      ? 'Для доступа требуется авторизация'
                      : 'Ошибка загрузки данных. Попробуйте позже.'}
                  </div>
                )}

                {!loading && characters.length === 0 ? (
                  <div className={styles.emptyState}>
                    <p>У вас пока нет персонажей</p>
                    {characterCreationStatus.can_create && (
                      <Button
                        variant="primary"
                        size="medium"
                        onClick={handleCreationClick}
                      >
                        Создать персонажа
                      </Button>
                    )}
                    {!characterCreationStatus.can_create && (
                      <p className={styles.limitInfo}>
                        Достигнут лимит персонажей ({characterCreationStatus.max_characters})
                      </p>
                    )}
                  </div>
                ) : (
                  <div className={styles.charactersGrid}>
                    {characters.map((character) => (
                      <CharacterCard
                        key={character.id}
                        character={character}
                        onCharacterUpdated={(updatedCharacter) => {
                          // Мгновенно помечаем оффлайн в кэше, refetch догонит фоном
                          dispatch(characterApi.util.updateQueryData('getMyCharacters', undefined, (draft) => {
                            const idx = draft.findIndex((c) => c.id === updatedCharacter.id);
                            if (idx !== -1) {
                              draft[idx] = { ...draft[idx], ...updatedCharacter };
                            }
                          }));
                          dispatch(characterApi.util.invalidateTags(['MyCharacters']));
                        }}
                      />
                    ))}
                  </div>
                )}

                <div className={styles.actions}>
                  <div className={styles.actionButtons}>
                    {characterCreationStatus.can_create && (
                      <Button
                        variant="primary"
                        size="medium"
                        onClick={handleCreationClick}
                        className={styles.actionButton}
                      >
                        Создать нового персонажа
                      </Button>
                    )}
                    {characters.some((char) => char.is_main !== true) && (
                      <Button
                        variant="secondary"
                        size="medium"
                        onClick={handleDetachmentClick}
                        className={styles.actionButton}
                      >
                        Открепить персонажа
                      </Button>
                    )}
                    {canShowAttachmentButton() && (
                      <Button
                        variant="secondary"
                        size="medium"
                        onClick={handleAttachmentClick}
                        className={styles.actionButton}
                      >
                        Прикрепить персонажа
                      </Button>
                    )}
                    {canShowTransferCurrencyButton() && (
                      <Button
                        variant="secondary"
                        size="medium"
                        onClick={handleTransferClick}
                        className={styles.actionButton}
                      >
                        Перевод валюты между персонажами
                      </Button>
                    )}
                  </div>
                </div>
              </>
            )}

          {activeTab === 'currency' && (
            <CurrencyExchangeForm
              key={`currency-${refreshTrigger.currency || 0}`}
              onSuccess={handleCurrencyExchangeSuccess}
              onCancel={() => setSearchParams({ tab: 'characters' })}
              characters={characters}
            />
          )}
          {activeTab !== 'characters' &&
            activeTab !== 'currency' &&
            activeTab !== 'referrals' &&
            activeTab !== 'play' && (
              <div className={styles.tabContent}>
                <div className={styles.tabPlaceholder}>
                  {activeTab === 'game' && <h3>Игровые услуги</h3>}
                  {activeTab === 'donations' && <h3>Пожертвования</h3>}
                  <p>Этот раздел находится в разработке</p>
                </div>
              </div>
            )}
          {activeTab === 'referrals' && (
            <ReferralsPage 
              key={`referrals-${refreshTrigger.referrals || 0}`}
            />
          )}
        </Card>
      </div>
    </div>
  );
};
const CharactersPage = withBaseMainPage(CharactersPageComponent);

export { CharactersPage };

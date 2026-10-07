import { config } from '../../../shared/config/env/env';
import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import styles from '../HousePage.module.css';
import btn from '../../../shared/styles/buttons.module.css';

const pct = (v) => Math.round((v || 0) * 100);

export const HouseInsideView = ({
  viewedHouse,
  isOwner,  
  requests,
  houseFurniture,
  myFurniture,
  maxGuests,
  activeTab,
  setActiveTab,
  busyItemId,
    busyAcceptId,
  busyRejectId,
  busyGuestId,
  isExiting,
  isUpdatingWallpaper,
  selectedWallpaperFile,
  currentError,
  handleExit,
  handleInstall,
  handleUninstall,
  handleAcceptRequest,
  handleRejectRequest,
  handleKickGuest,
  handleWallpaperFileChange,
  handleUploadWallpaper,
  handleDeleteWallpaper,
}) => {
    const bonuses = viewedHouse.bonuses || {};
  const guestsCount = viewedHouse.guests_count || 0;
  const guests = viewedHouse.guests || [];

  const renderBonuses = () => (
    <div className={styles.bonuses}>
      <div>
        Комплект мебели: <span className={styles.green}>+{bonuses.health || 0}%</span>{' '}
        <span className={styles.red}>+{bonuses.tiredness || 0}%</span>{' '}
        <span className={styles.blue}>+{bonuses.mana || 0}%</span>
      </div>
    </div>
  );

  const renderGuestsList = (withKick) => (
    guests.length > 0 && (
      <div className={styles.guestsList}>
        {guests.map(g => (
          <div key={g.character_id} className={styles.guestRow}>
            <span>{g.name}</span>
            {withKick && (
              <button
                className={btn.textLinkDanger}
                disabled={busyGuestId === g.character_id}
                onClick={() => handleKickGuest(g.character_id)}
              >
                Выгнать
              </button>
            )}
          </div>
        ))}
      </div>
    )
  );

  const renderRequests = () => (
    requests.length > 0 && (
      <div className={styles.requestsList}>
        {requests.map(r => (
          <div key={r.id} className={styles.requestRow}>
            <span>{r.name} стучится...</span>
            <button
              className={btn.textLinkDanger}
              disabled={busyAcceptId === r.id}
              onClick={() => handleAcceptRequest(r.id)}
            >
              Впустить
            </button>
            <button
              className={btn.textLinkDanger}
              disabled={busyRejectId === r.id}
              onClick={() => handleRejectRequest(r.id)}
            >
              Отказать
            </button>
          </div>
        ))}
      </div>
    )
  );

  const renderExitButton = () => (
    <button
      className={`${btn.textLinkDanger} ${styles.exitButton}`}
      onClick={handleExit}
      disabled={isExiting}
    >
      • Выйти из дома
    </button>
  );

  const renderOwnerLeftPanel = () => (
    <>
      <div className={styles.tabLine}>
        {activeTab === 'house' ? (
          <strong>Дом</strong>
        ) : (
          <button className={btn.textLinkDanger} onClick={() => setActiveTab('house')}>
            Дом
          </button>
        )}
        {' • '}
        {activeTab === 'wallpaper' ? (
          <strong>Сменить обои</strong>
        ) : (
          <button className={btn.textLinkDanger} onClick={() => setActiveTab('wallpaper')}>
            Сменить обои
          </button>
        )}
        {' • '}
        {activeTab === 'backpack' ? (
          <strong>Мебель в рюкзаке</strong>
        ) : (
          <button className={btn.textLinkDanger} onClick={() => setActiveTab('backpack')}>
            Мебель в рюкзаке
          </button>
        )}
      </div>

      {activeTab === 'house' ? (
        <>
          {renderBonuses()}
          <div className={styles.guestsCount}>
            Гости ({guestsCount}/{maxGuests})
          </div>
          {renderGuestsList(true)}
          {renderRequests()}
          {renderExitButton()}
        </>
      ) : activeTab === 'wallpaper' ? (
        <div className={styles.wallpaperSection}>
          <div className={styles.wallpaperControls}>
            <span className={styles.fileName}>
              {selectedWallpaperFile ? selectedWallpaperFile.name : "Файл не выбран"}
            </span>
            <label htmlFor="wallpaper-upload" className={`${btn.gameButton} ${btn.sizeSmall}`}>
              Выберите файл
            </label>
            <input
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif"
              onChange={handleWallpaperFileChange}
              className={styles.fileInput}
              id="wallpaper-upload"
            />
            <div className={styles.wallpaperButtons}>
              <button
                className={`${btn.gameButton} ${btn.sizeSmall}`}
                onClick={handleUploadWallpaper}
                disabled={isUpdatingWallpaper}
              >
                Загрузить
              </button>
              {viewedHouse.wallpaper_photo_id && (
                <button
                  className={`${btn.gameButton} ${btn.sizeSmall} ${btn.colorDanger}`}
                  onClick={handleDeleteWallpaper}
                  disabled={isUpdatingWallpaper}
                >
                  Удалить
                </button>
              )}
            </div>
          </div>
        </div>
      ) : myFurniture.length === 0 ? (
        <div className={styles.noItems}>Нет мебели в рюкзаке</div>
      ) : (
        myFurniture.map(item => (
          <div className={styles.backpackRow} key={item.inventory_item_id}>
            <span>{item.name} [{item.wear}/{item.max_wear ?? '-'}]</span>
            <button
              className={btn.textLinkDanger}
              disabled={busyItemId === item.inventory_item_id}
              onClick={() => handleInstall(item.inventory_item_id)}
            >
              В дом
            </button>
          </div>
        ))
      )}
    </>
  );

  const renderGuestLeftPanel = () => (
    <>
      <div className={styles.ownerLine}>
        Хозяин дома: <strong>{viewedHouse.owner_name || '—'}</strong>
      </div>
      {renderBonuses()}
      <div className={styles.guestsCount}>
        Гости ({guestsCount}/{maxGuests})
      </div>
      {renderGuestsList(false)}
      {renderExitButton()}
    </>
  );

  return (
    <div
      className={styles.wrapper}
      style={
        viewedHouse.wallpaper_photo_id
          ? {
              backgroundImage: `url(${config.FILE_API_BASE_URL}/${viewedHouse.wallpaper_photo_id}/content), url('/images/station/background.jpg')`,
              backgroundSize: 'cover, auto',
              backgroundPosition: 'center, top left',
              backgroundRepeat: 'no-repeat, repeat',
            }
          : undefined
      }
    >
      <ErrorToast message={currentError} />
      <div className={styles.contentBox}>
        <div className={styles.twoBoxes}>
          {/* Левая рамка */}
          <div className={styles.borderBox}>
            <table className={`${styles.infoTable} ${styles.alignLeft}`}>
              <colgroup>
                <col style={{ width: '100%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Дом №{viewedHouse.number}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className={styles.houseInfo}>
                    {isOwner ? renderOwnerLeftPanel() : renderGuestLeftPanel()}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Правая рамка — установленная мебель */}
          <div className={styles.borderBox}>
            <table className={`${styles.housesTable} ${styles.alignLeft}`}>
              <colgroup>
                <col style={{ width: '35%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Предмет</th>
                  <th>Износ</th>
                  <th></th>
                  <th></th>
                  <th></th>
                  <th className={styles.columnHeader}>
                    {viewedHouse.current_volume}/{viewedHouse.capacity}
                  </th>
                </tr>
              </thead>
              <tbody>
                {houseFurniture.length === 0 ? (
                  <tr>
                    <td colSpan={6} className={styles.noItems}>В доме нет мебели</td>
                  </tr>
                ) : (
                  houseFurniture.map(item => {
                    const p = item.ability_parameters || {};
                    return (
                      <tr key={item.inventory_item_id}>
                        <td>{item.name}</td>
                        <td>{item.wear}/{item.max_wear ?? '-'}</td>
                        <td className={pct(p.health_percentage) > 0 ? styles.green : undefined}>
                          {pct(p.health_percentage)}/{pct(p.health_percentage_weared)}
                        </td>
                        <td className={pct(p.tiredness_percentage) > 0 ? styles.red : undefined}>
                          {pct(p.tiredness_percentage)}/{pct(p.tiredness_percentage_weared)}
                        </td>
                        <td className={pct(p.mana_percentage) > 0 ? styles.blue : undefined}>
                          {pct(p.mana_percentage)}/{pct(p.mana_percentage_weared)}
                        </td>
                        <td>
                          {isOwner && (
                            <button
                              className={btn.textLinkDanger}
                              disabled={busyItemId === item.inventory_item_id}
                              onClick={() => handleUninstall(item.inventory_item_id)}
                            >
                              Забрать
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
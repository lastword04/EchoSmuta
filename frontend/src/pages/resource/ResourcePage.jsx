import { useMiningLogic } from "./hooks/useMiningLogic";
import { resourceIcon, DEFAULT_RESOURCE_ICON } from "../../shared/config/ui/resourceIcons";
import styles from "./ResourcePage.module.css";
import { getResourceBySlug } from "../../shared/config/locations/locations";
import { 
  MINING_UI,
  MINING_PATHS,
  LOCATION_COLUMN_WIDTHS,
} from '../../entities/character/config/mining';

function ResourcePage({ character, onRefresh }) {
  const {
    resourcesData,
    miningId,
    miningMessage,
    endTime,
    countdown,
    miningResult,
    captchaData,
    captchaInput,
    isCaptchaFetching,
    isCollapsed,
    setIsCollapsed,
    canMine,
    errorMessage,
    isMiningRequestInProgress,
    captchaInputRef,
    handleInputChange,
    handleMine,
    fetchNewCaptcha,
  } = useMiningLogic({ character, onRefresh });

  if (!resourcesData) return null;

  const { resources = [], character_location_level } = resourcesData;
  const resource = character ? getResourceBySlug(character.location_slug) : null;
  const currentLocation = character?.location_slug;
  // Для ебучей рыбы
  const isLakeLocation = currentLocation === '2.4.lake'; 
  const locationClass = currentLocation
  ? styles[`loc_${currentLocation.replace(/\./g, '_')}`]
  : '';
  const columnWidths = LOCATION_COLUMN_WIDTHS[currentLocation] || [
    "12.54%", "38.66%", "25.11%", "12.69%", "11%",
  ];
  const bgUrl = character ? MINING_PATHS.LOCATION_BG(character.location_slug) : "";
  const getResourceCount = (count) => count > 0 ? count : "Выработано";

  return (
    <div className={styles.mainResource} style={{ backgroundImage: `url("${bgUrl}")` }}>
      <div className={styles.wrapper}>
        <div className={styles.contentBox}>
          <div className={styles.leftRightLayout}>
            <div className={styles.borderBox}>
              <table className={`${styles.table} ${locationClass || ''}`}>
                <colgroup>
                  {columnWidths.map((width, index) => (
                    <col key={index} style={{ width }} />
                  ))}
                </colgroup>
                <thead>
                  <tr>
                    <th></th>
                    <th>{resource?.resourceName}</th>
                    <th>Доступно</th>
                    <th>Успех</th>
                    <th
                      style={{ cursor: "pointer" }}
                      onClick={() => setIsCollapsed((prev) => !prev)}
                      title="Скрыть/показать ресурсы"
                    >
                      {isCollapsed ? "▼" : "▲"}
                    </th>
                  </tr>
                </thead>
                <tbody className={isCollapsed ? styles.hidden : ""}>
                  {resources.map((res) => (
                    <tr key={res.resource_slug}>
                      <td>
                        <img
                          src={resourceIcon(res.resource_slug)}
                          onError={(e) => { e.target.onerror = null; e.target.src = DEFAULT_RESOURCE_ICON; }}
                          alt={res.resource_name}
                          className={`${styles.resourceImage} ${isLakeLocation ? styles.resourceImageWide : ''}`}
                        />
                      </td>
                      <td>{res.resource_name}</td>
                      <td>{getResourceCount(res.current_amount)}</td>
                      <td>{(res.chance * 100).toFixed(0)}%</td>
                      <td>{res.amount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className={styles.infoBox}>
              {resource && (
                <div>
                  <div>Ваше умение {resource?.profession}: {character_location_level?.level}</div>
                  <div>Ваш опыт {resource?.profession}: {character_location_level?.experience}</div>
                </div>
              )}

              {miningResult && (
                <div style={{ color: MINING_UI.ERROR_COLOR, marginTop: MINING_UI.MARGIN_TOP }}>
                  {miningResult}
                </div>
              )}

              {errorMessage && !miningMessage && (
                <div style={{ color: MINING_UI.ERROR_COLOR, marginTop: MINING_UI.MARGIN_TOP }}>
                  {errorMessage}
                </div>
              )}

              {miningMessage && endTime && (
                <div style={{ color: MINING_UI.TIMER_COLOR, marginTop: MINING_UI.MARGIN_TOP }}>
                  {miningMessage} {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
                </div>
              )}

              {canMine && captchaData && !miningId && (
                <div>
                  <form onSubmit={(e) => { e.preventDefault(); handleMine(); }}>
                    <div className={styles.captchaMiniRow}>
                      <img
                        src={captchaData.image_url}
                        alt="Капча"
                        className={styles.captchaMiniImage}
                        onClick={async () => {
                          if (isCaptchaFetching) return;
                          await fetchNewCaptcha();
                        }}
                        title="Нажмите для обновления капчи"
                      />
                      <input
                        type="text"
                        placeholder="Код"
                        className={styles.captchaMiniInput}
                        value={captchaInput}
                        onChange={handleInputChange}
                        autoComplete="off"
                        ref={captchaInputRef}
                      />
                    </div>
                    <button
                      type="submit"
                      className={styles.actionButton}
                      disabled={isMiningRequestInProgress || isCaptchaFetching || !captchaInput}
                    >
                      {resource?.action}
                    </button>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResourcePage;
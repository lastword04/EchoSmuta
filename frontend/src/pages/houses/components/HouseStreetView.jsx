import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { intInputHandler } from '../../../shared/lib/validation/numberInput';
import styles from '../HousePage.module.css';
import btn from '../../../shared/styles/buttons.module.css';

export const HouseStreetView = ({
  houses,
  housePrice,
  isBuying,
  busyHouseId,
  knockHouseNumber,
  setKnockHouseNumber,
  isKnocking,
  currentError,
  handleBuy,
  handleEnter,
  handleKnock,
}) => {
  return (
    <div className={styles.wrapper}>
      <ErrorToast message={currentError} />
      <div className={styles.contentBox}>
        <div className={styles.tables}>          

          <div className={styles.availability}>
            Стоимость дома: {housePrice} дт.
          </div>

          <div className={styles.enterButton}>
            <button
              className={`${btn.simpleButton} ${btn.simpleButtonGold}`}
              onClick={handleBuy}
              disabled={isBuying}
            >
              Купить дом
            </button>
          </div>

          {houses.length > 0 && (
            <>
              <div className={styles.availability} style={{ marginTop: '20px' }}>
                Ваши дома:
              </div>

              <div className={styles.borderBox}>
                <table className={styles.housesTable}>
                  <colgroup>
                    <col style={{ width: '14%' }} />
                    <col style={{ width: '23%' }} />
                    <col style={{ width: '23%' }} />
                    <col style={{ width: '23%' }} />
                    <col style={{ width: '17%' }} />
                  </colgroup>
                  <thead>
                    <tr>
                      <th>№</th>
                      <th>Здоровье</th>
                      <th>Усталость</th>
                      <th>Мана</th>                      
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {houses.map(house => {
                      const bonuses = house.bonuses || {};
                      return (
                        <tr key={house.id}>
                          <td>{house.number}</td>
                          <td className={styles.bonusCell}>+{bonuses.health || 0}%</td>
                          <td className={styles.bonusCell}>+{bonuses.tiredness || 0}%</td>
                          <td className={styles.bonusCell}>+{bonuses.mana || 0}%</td>                          
                          <td className={styles.actionCell}>
                            <button
                              className={btn.textLinkDanger}
                              onClick={() => handleEnter(house.id)}
                              disabled={busyHouseId === house.id}
                            >
                              Войти
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <div className={styles.knockRow}>
            <span>Зайти в гости в дом</span>
            <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={knockHouseNumber}
                onChange={intInputHandler(setKnockHouseNumber, 7, { strip: true })}
                className={styles.knockInput}
                placeholder="№"
            />
            <button
              className={btn.gameButton}
              onClick={handleKnock}
              disabled={isKnocking}
            >
              Постучать
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
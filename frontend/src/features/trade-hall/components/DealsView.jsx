import { useDealsLogic } from './hooks/useDealsLogic';
import { CardOverlays } from './deal-ui/CardOverlays';
import { DealBackpack } from './deal-ui/DealBackpack';
import { PartnerSelection } from './deal-ui/PartnerSelection';
import { DealOfferTable } from './deal-ui/DealOfferTable';
import styles from "./DealsView.module.css";
import btn from "../../../shared/styles/buttons.module.css";

function DealsView({ character, onRefresh }) {
  const logic = useDealsLogic(character, onRefresh);

  if (logic.isLoading) return null;

  const cardOverlays = (
    <CardOverlays
      selectedItem={logic.selectedItem}
      selectedResource={logic.selectedResource}
      character={character}
      onCloseItem={() => logic.setSelectedItem(null)}
      onCloseResource={logic.closeResource}
    />
  );

  // Единый блок рюкзака для обоих экранов (выбор партнёра и активная сделка)
  const backpack = (
    <DealBackpack
      myItems={logic.myItems}
      myResources={logic.myResources}
      myDealItems={logic.myDealItems}
      isItemAsset={logic.isItemAsset}
      resFree={logic.resFree}
      moneyInput={logic.moneyInput}
      setMoneyInput={logic.setMoneyInput}
      selectedCurrency={logic.selectedCurrency}
      setSelectedCurrency={logic.setSelectedCurrency}
      hasGold={logic.hasGold}
      leftDisabled={logic.leftDisabled}
      getQty={logic.getQty}
      setQty={logic.setQty}
      handleAddMoney={logic.handleAddMoney}
      handleAddItem={logic.handleAddItem}
      handleAddResource={logic.handleAddResource}
      openResource={logic.openResource}
      setSelectedItem={logic.setSelectedItem}
    />
  );

  // --- Экран выбора партнера (нет активной сделки) ---
  if (!logic.activeDeal) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.leftRightLayout}>
          {backpack}
          <PartnerSelection
            nearbyPartners={logic.nearbyPartners}
            selectedPartnerId={logic.selectedPartnerId}
            setSelectedPartnerId={logic.setSelectedPartnerId}
            isProcessing={logic.isProcessing}
            handleSelectPartner={logic.handleSelectPartner}
          />
        </div>
        {cardOverlays}
      </div>
    );
  }

  // --- Экран активной сделки ---
  return (
    <div className={styles.wrapper}>
      <div className={styles.leftRightLayout}>
        {backpack}
        <div className={styles.rightColumn}>
          {/* Моя сторона */}
          <div className={styles.sideHeader}>
            Ваша сторона - {logic.iConfirmed ? <span className={styles.statusGreen}>Вы подтвердили сделку</span> : <span className={styles.statusRed}>Вы не подтвердили сделку</span>}
          </div>
          
          <DealOfferTable
            offer={logic.myOffer}
            items={logic.myDealItems}
            isEditable={logic.isEditable}
            isProcessing={logic.isProcessing}
            onRemoveDucats={logic.handleRemoveDucats}
            onRemoveGold={logic.handleRemoveGold}
            onRemoveItem={logic.handleRemoveItem}
            onRemoveResource={logic.handleRemoveResource}
            onItemClick={logic.openDealItemCard}
            onResourceClick={logic.openResource}
            displayName={logic.displayName}
            isItemAsset={logic.isItemAsset}
          />

          {/* Налог */}
          {logic.partnerOffer && parseFloat(logic.partnerOffer.ducats_escrowed || 0) > 0 && logic.myTax > 0 && (
            <div className={styles.taxRow}>
              Налог, который вы должны уплатить: {logic.myTax.toFixed(2)} дт.
            </div>
          )}

          {/* Кнопки управления */}
          {!logic.dealFinished && (
            <div className={styles.confirmRow}>
              <button className={btn.gameButton} onClick={logic.handleConfirm} disabled={!logic.isEditable || logic.isProcessing || logic.iConfirmed}>Подтвердить сделку</button>
              <button className={`${btn.gameButton}`} onClick={logic.handleCancel} disabled={logic.isProcessing}>Отменить сделку</button>
            </div>
          )}
          {logic.dealFinished && (
            <div className={styles.confirmRow}>
              <button className={`${btn.gameButton}`} onClick={logic.handleCancel} disabled={logic.isProcessing}>Отменить сделку</button>
            </div>
          )}

          {/* Сторона партнера */}
          <div className={styles.sideHeader}>
            {logic.partnerName} - {logic.partnerConfirmed ? <span className={styles.statusGreen}>Партнер подтвердил сделку</span> : <span className={styles.statusRed}>Партнер не подтвердил сделку</span>}
          </div>

          <DealOfferTable
            offer={logic.partnerOffer}
            items={logic.partnerDealItems}
            isEditable={false}
            isProcessing={logic.isProcessing}
            onItemClick={logic.openDealItemCard}
            onResourceClick={logic.openResource}
            displayName={logic.displayName}
            isItemAsset={logic.isItemAsset}
          />

          {/* Ошибки */}
          <div style={{ minHeight: "20px" }}>
            {logic.errorMessage && <span className={styles.statusRed}>{logic.errorMessage}</span>}
          </div>
        </div>
      </div>
      {cardOverlays}        
    </div>
  );
}

export default DealsView;
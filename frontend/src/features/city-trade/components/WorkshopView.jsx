import { CraftingTable } from './workshop/components/CraftingTable';
import { RecipesTable } from './workshop/components/RecipesTable';
import { CraftingForm } from './workshop/components/CraftingForm';
import { useWorkshopLogic } from './workshop/hooks/useWorkshopLogic';
import { MINING_REGEX } from '../../../entities/character/config/mining';
import btn from '../../../shared/styles/buttons.module.css';
import styles from './WorkshopView.module.css';

function WorkshopView({ locationSlug, onRefresh, character }) {
  // Вся магия теперь здесь, в одной строке:
  const logic = useWorkshopLogic({ locationSlug, onRefresh, character });

  const {
    activeTab,
    selectedRecipe, setSelectedRecipe,
    selectedStartCreatingId, setSelectedStartCreatingId,
    captchaData, captchaInput, setCaptchaInput,
    errorMessage, successMessage, craftingResult,
    craftingId, craftingMessage, endTime, isCheckingResult,
    isInitialized, texts, locationConfig,
    minLevel, isLevelAllowed, isTiredAllowed,
    isLicenseLoading, isLicenseValid, isReadyForCaptcha,
    canShowForm, isInitialDataLoading,
    countdown, startedCrafting, recipes, stats,
    handleTabClick, handleCaptchaRefresh, handleCreate,
    captchaFailed, isCaptchaLoading,
    isRefreshingTab
  } = logic;

  if (!isInitialized || isInitialDataLoading) return null;

  return (
    <div className={styles.workshopContainer}>
      <div className={styles.tabs}>
        <button 
          className={`${btn.gameButton} ${activeTab === 'crafting' ? btn.gameButtonActive : ''}`} 
          onClick={() => handleTabClick('crafting')} 
          disabled={isRefreshingTab}
        >
          {texts.craftingTab}
        </button>
        <span className={styles.dot}>•</span>
        <button 
          className={`${btn.gameButton} ${activeTab === 'recipes' ? btn.gameButtonActive : ''}`} 
          onClick={() => handleTabClick('recipes')} 
          disabled={isRefreshingTab}
        >
          {texts.workshopTab}
        </button>
      </div>

      <div className={styles.mainContent}>
        <div className={styles.leftColumn}>
          {activeTab === 'crafting' ? (
            <CraftingTable 
              startedCrafting={startedCrafting} 
              selectedStartCreatingId={selectedStartCreatingId} 
              onRecipeSelect={(id) => setSelectedStartCreatingId(id === selectedStartCreatingId ? null : id)} 
              locationSlug={locationSlug} 
              character={character} 
              isCraftingInProgress={Boolean(craftingId)}
            />
          ) : (
            <RecipesTable 
              recipes={recipes} 
              startedCrafting={startedCrafting} 
              selectedRecipe={selectedRecipe} 
              onRecipeSelect={(id) => setSelectedRecipe(id === selectedRecipe ? null : id)} 
              locationSlug={locationSlug} 
              character={character} 
              isCraftingInProgress={Boolean(craftingId)}
            />
          )}
        </div>

        <div className={styles.rightColumn}>
          <div className={styles.infoBox}>
            <div className={styles.craftTable}>
              {stats && locationConfig?.profession && (
                <div className={styles.statsInfo}>
                  <div>{locationConfig.profession.skillLabel}: {stats.level}</div>
                  <div>{locationConfig.profession.expLabel}: {stats.experience}</div>
                </div>
              )}

              {craftingResult && <div className={styles.successMessage}>{craftingResult}</div>}
              
              {!isCheckingResult && !craftingMessage && !isLevelAllowed && (
                <div className={styles.errorMessage}>Крафтить можно с {minLevel}-го уровня</div>
              )}

              {!isCheckingResult && !craftingMessage && !isTiredAllowed && (
                <div className={styles.errorMessage}>Вы слишком устали. Отдохните, чтобы продолжить работу</div>
              )}
              
              {errorMessage && <div className={styles.errorMessage}>{errorMessage}</div>}
              
              {successMessage && !craftingMessage && !craftingResult && (
                <div className={styles.successMessage}>{successMessage}</div>
              )}

              {craftingMessage && endTime && (
                <div className={styles.timerMessage}>
                  {craftingMessage} Осталось {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
                </div>
              )}

              {!craftingId && !isCheckingResult && !isLicenseLoading && !isLicenseValid && (
                <div className={styles.errorMessage}>Срок действия лицензии истёк.</div>
              )}

              {isReadyForCaptcha && !captchaData && captchaFailed && (
                <button className={btn.gameButton} onClick={handleCaptchaRefresh}>
                  Обновить капчу
                </button>
              )}

              {canShowForm && (
                <CraftingForm
                  captchaData={captchaData}
                  captchaInput={captchaInput}
                  isCaptchaLoading={isCaptchaLoading}
                  isSubmitting={logic.isSubmitting}
                  activeTab={activeTab}
                  selectedStartCreatingId={selectedStartCreatingId}
                  selectedRecipe={selectedRecipe}
                  onSubmit={handleCreate}
                  onInputChange={(event) => {
                    if (MINING_REGEX.CAPTCHA_INPUT.test(event.target.value)) setCaptchaInput(event.target.value);
                  }}
                  onCaptchaRefresh={handleCaptchaRefresh}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkshopView;
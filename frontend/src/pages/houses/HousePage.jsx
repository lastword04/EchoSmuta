import { useHouseActions } from './hooks/useHouseActions';
import { HouseStreetView } from './components/HouseStreetView';
import { HouseInsideView } from './components/HouseInsideView';

function HousePage({ character }) {
  const actions = useHouseActions(character); 

  if (!character || !actions.statusData) return null;

  if (actions.isInsideHouse && actions.viewedHouse) {
    return (
      <HouseInsideView
        viewedHouse={actions.viewedHouse}
        isOwner={actions.isOwner}
        requests={actions.requests}
        houseFurniture={actions.houseFurniture}
        myFurniture={actions.myFurniture}
        maxGuests={actions.maxGuests}
        activeTab={actions.activeTab}
        setActiveTab={actions.setActiveTab}
        busyItemId={actions.busyItemId}
        busyAcceptId={actions.busyAcceptId}
        busyRejectId={actions.busyRejectId}
        busyGuestId={actions.busyGuestId}
        isExiting={actions.isExiting}
        isUpdatingWallpaper={actions.isUpdatingWallpaper}
        selectedWallpaperFile={actions.selectedWallpaperFile}
        currentError={actions.currentError}
        handleExit={actions.handleExit}
        handleInstall={actions.handleInstall}
        handleUninstall={actions.handleUninstall}
        handleAcceptRequest={actions.handleAcceptRequest}
        handleRejectRequest={actions.handleRejectRequest}
        handleKickGuest={actions.handleKickGuest}
        handleWallpaperFileChange={actions.handleWallpaperFileChange}
        handleUploadWallpaper={actions.handleUploadWallpaper}
        handleDeleteWallpaper={actions.handleDeleteWallpaper}
      />
    );
  }

  return (
    <HouseStreetView
      houses={actions.houses}
      housePrice={actions.housePrice}
      isBuying={actions.isBuying}
      busyHouseId={actions.busyHouseId}
      knockHouseNumber={actions.knockHouseNumber}
      setKnockHouseNumber={actions.setKnockHouseNumber}
      isKnocking={actions.isKnocking}
      currentError={actions.currentError}
      handleBuy={actions.handleBuy}
      handleEnter={actions.handleEnter}
      handleKnock={actions.handleKnock}
    />
  );
}

export default HousePage;
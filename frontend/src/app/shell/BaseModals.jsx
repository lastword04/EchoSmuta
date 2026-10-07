import { useCallback } from 'react';
import { useEscapeKey } from '../../shared/hooks/ui/useEscapeKey';
import { NotebookModal } from '../../widgets/CharacterPanel/NotebookModal/NotebookModal';
import { CityMapModal } from '../../widgets/CharacterPanel/CityMapModal/CityMapModal';
import { CharacterInfoModal } from '../../widgets/CharacterPanel/CharacterInfoModal/CharacterInfoModal';
import { OutskirtsModal } from '../../widgets/CharacterPanel/OutskirtsModal/OutskirtsModal';
import { MailModal } from '../../widgets/TopBar/MailModal/MailModal';
import { ImprovementsModal } from '../../widgets/CharacterPanel/ImprovementsModal/ImprovementsModal';
import { FriendsModal } from '../../widgets/FriendsModal/FriendsModal';
import { InventoryModal } from '../../widgets/InventoryModal/InventoryModal';
import { MagicModal } from '../../widgets/CharacterPanel/MagicModal/MagicModal';
import { isResourceLocation } from '../../shared/config/locations/locations';
import { ModalOverlay } from '../../shared/ui/ModalOverlay/ModalOverlay';

export default function Modals({
  activeModal,
  abilitySkills,
  weaponSkills,  
  doNotReceive,
  setDoNotReceive,
  character,
  setActiveModal,
  handleOpenFriends,
  handleOpenMagic,
  handleSaveUpSkills,
  locationCounts,
  handleLocationChange,
  panelHeight,
}) {
  const close = useCallback(() => setActiveModal(null), [setActiveModal]);
  useEscapeKey(close, Boolean(activeModal));

  if (!activeModal) return null;

  // Полноэкранный режим: Окрестности или карта, открытая из resource-локации
  const inOutskirts =
    activeModal === 'OUTSKIRTS_MODAL' ||
    (activeModal === 'MAP_MODAL' && isResourceLocation(character?.location_slug));

  const renderModal = () => {
    switch (activeModal) {
      case 'NOTEBOOK_MODAL':
        return <NotebookModal onClose={close} />;
      case 'OUTSKIRTS_MODAL':
      case 'MAP_MODAL':
        return inOutskirts ? (
          <OutskirtsModal onClose={close} handleLocationChange={handleLocationChange} setActiveModal={setActiveModal} />
        ) : (
          <CityMapModal onClose={close} handleLocationChange={handleLocationChange} setActiveModal={setActiveModal} counts={locationCounts} />
        );
      case 'CITY_MAP_MODAL':
        return <CityMapModal onClose={close} handleLocationChange={handleLocationChange} setActiveModal={setActiveModal} counts={locationCounts} />;
      case 'SETTINGS_MODAL':
        return <CharacterInfoModal onClose={close} />;
      case 'FRIENDS_MODAL':
        return <FriendsModal onClose={close} doNotReceive={doNotReceive} setDoNotReceive={setDoNotReceive} />;
      case 'INVENTORY_MODAL':
        return (
          <InventoryModal
            onClose={close}
            character={character}
            weight={character?.weight}
            maxWeight={character?.max_weight}
            setActiveModal={setActiveModal}
            handleOpenMagic={handleOpenMagic}
          />
        );
      case 'MAGIC_MODAL':
        return <MagicModal character={character} onClose={close} />;
      case 'MAIL_MODAL':
        return <MailModal onClose={close} onOpenFriends={handleOpenFriends} />;
      case 'SKILLS_MODAL':
        return (
          <ImprovementsModal
            
            character={character}
            onClose={close}
            freePoints={abilitySkills}
            freeMasteryPoints={weaponSkills}
            onSave={handleSaveUpSkills}
          />
        );
      default:
        // Неизвестный/нереализованный тип (PARAMETERS_MODAL и т.д.) — не рендерим пустой оверлей
        return null;
    }
  };

  const content = renderModal();
  if (!content) return null;

  return (
    <ModalOverlay inOutskirts={inOutskirts} panelHeight={panelHeight} onClose={close}>
      {content}
    </ModalOverlay>
  );
}

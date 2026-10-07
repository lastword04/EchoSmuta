import { useMediaQuery } from '../../shared/hooks/ui/useMediaQuery';
import { useCharacterImage } from '../../entities/character/hooks/useCharacterImage';
import { MobileCharacterPanel } from './MobileCharacterPanel';
import { DesktopCharacterPanel } from './DesktopCharacterPanel';
import { usePanelMenu } from './hooks/usePanelMenu';

const SQUARE_CONFIG = [
  { content: null },
  { content: null },
  { className: 'invisibleSquare', content: null },
  { className: 'invisibleSquare', content: null },
  { content: null },
  { content: null },
  { content: null },
  { content: null },
];

export const CharacterPanel = ({ character, onMenuItemClick, handleUpSkillsButtonClick, isShowUpSkills }) => {
  const isMobile = useMediaQuery('(max-width: 950px)');
  
  const {
    showMenu,   
    menuRef,
    handleControlButtonMouseEnter,
    handleControlButtonMouseLeave,
    handleMenuMouseEnter,
    handleMenuMouseLeave,
    handleControlButtonClick,
    handleMenuItemClickInternal,
  } = usePanelMenu(isMobile, onMenuItemClick);
 

  const { 
    image: characterImage,     
    error: imageError,
    handleImageError
  } = useCharacterImage(character?.photo_id);


  if (!character) {
    return null;
  }

  if (isMobile) {
    return (
      <MobileCharacterPanel
        character={character}
        characterImage={characterImage}      
        imageError={imageError}   
        handleImageError={handleImageError}     
        squareConfig={SQUARE_CONFIG}
        isShowUpSkills={isShowUpSkills}
        handleUpSkillsButtonClick={handleUpSkillsButtonClick}
      />
    );
  }

  return (
    <DesktopCharacterPanel
      character={character}
      characterImage={characterImage}     
      imageError={imageError}     
      handleImageError={handleImageError} 
      squareConfig={SQUARE_CONFIG}
      showMenu={showMenu}      
      menuRef={menuRef}
      handleControlButtonMouseEnter={handleControlButtonMouseEnter}
      handleControlButtonMouseLeave={handleControlButtonMouseLeave}
      handleControlButtonClick={handleControlButtonClick}
      handleMenuMouseEnter={handleMenuMouseEnter}
      handleMenuMouseLeave={handleMenuMouseLeave}
      handleMenuItemClickInternal={handleMenuItemClickInternal}          
      isShowUpSkills={isShowUpSkills}
      handleUpSkillsButtonClick={handleUpSkillsButtonClick}
    />
  );
};
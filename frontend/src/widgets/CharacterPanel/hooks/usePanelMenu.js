import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Владеет UI state меню CharacterPanel:
 * showMenu, isMenuPinned, isHovering + hover/click handlers.
 * 
 * Чистый UI state, не зависит от panelData, selectedItems, character.
 * 
 * @param {boolean} isMobile - мобильная версия
 * @param {Function} onMenuItemClick - callback от родителя при клике на пункт меню
 */
export const usePanelMenu = (isMobile, onMenuItemClick) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isMenuPinned, setIsMenuPinned] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const menuRef = useRef(null);

  // Закрытие меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        if (isMenuPinned) {
          setShowMenu(false);
          setIsMenuPinned(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuPinned]);

  // Синхронизация showMenu с isHovering (только desktop, не pinned)
  useEffect(() => {
    if (!isMenuPinned && !isMobile) {
      setShowMenu(isHovering);
    }
  }, [isHovering, isMenuPinned, isMobile]);

  const handleControlButtonMouseEnter = useCallback(() => {
    if (!isMobile && !isMenuPinned) {
      setIsHovering(true);
    }
  }, [isMobile, isMenuPinned]);

  const handleControlButtonMouseLeave = useCallback(() => {
    if (!isMobile && !isMenuPinned) {
      setIsHovering(false);
    }
  }, [isMobile, isMenuPinned]);

  const handleMenuMouseEnter = useCallback(() => {
    if (!isMobile && !isMenuPinned) {
      setIsHovering(true);
    }
  }, [isMobile, isMenuPinned]);

  const handleMenuMouseLeave = useCallback(() => {
    if (!isMobile && !isMenuPinned) {
      setIsHovering(false);
    }
  }, [isMobile, isMenuPinned]);

  const handleControlButtonClick = useCallback(() => {
    if (isMobile) return;
    
    if (isMenuPinned) {
      setIsMenuPinned(false);
      setShowMenu(false);
      setIsHovering(false);
    } else {
      setIsMenuPinned(true);
      setShowMenu(true);
      setIsHovering(false);
    }
  }, [isMobile, isMenuPinned]);

  const handleMenuItemClickInternal = useCallback((menuItem) => {
    if (onMenuItemClick) {
      onMenuItemClick(menuItem);
    }
    
    setShowMenu(false);
    setIsMenuPinned(false);
    setIsHovering(false);
  }, [onMenuItemClick]);

  return {
    showMenu,
    isMenuPinned,
    menuRef,
    handleControlButtonMouseEnter,
    handleControlButtonMouseLeave,
    handleMenuMouseEnter,
    handleMenuMouseLeave,
    handleControlButtonClick,
    handleMenuItemClickInternal,
  };
};
import { MenuItem } from '../../shared/ui/MenuItem/MenuItem';
import { useGetMyPanelsQuery } from '../../entities/character/api/panelApi';
import { menuItems } from '../../shared/config/ui/menuItems';
import styles from './MenuItemsList.module.css'; 

export const MenuItemsList = ({ onMenuItemClick, onCheckboxChange }) => {
  const { data: panelData } = useGetMyPanelsQuery();
  
  const selectedItems = panelData ? { first_item: panelData.first_item, second_item: panelData.second_item } : { first_item: null, second_item: null };

  const isItemChecked = (itemId) => selectedItems.first_item === itemId || selectedItems.second_item === itemId;
  
  const handleMenuItemClickInternal = (menuItem) => {
    if (onMenuItemClick) onMenuItemClick(menuItem);
  };

  const handleCheckboxChangeInternal = (itemId, isChecked) => {
    if (onCheckboxChange) onCheckboxChange(itemId, isChecked);
  };

  return (
    <div className={styles.menuItemsList}>
      {menuItems.map((menuItem) => (
        <MenuItem
          key={menuItem.id}
          item={menuItem}
          onClick={handleMenuItemClickInternal}
          isChecked={isItemChecked(menuItem.id)}
          onCheckboxChange={handleCheckboxChangeInternal}          
        />
      ))}
    </div>
  );
};
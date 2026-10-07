import React, { useState, useEffect } from "react";
import { ResourceBackpackComponent } from "./tabs/ResourceBackpackComponent";
import { EquipmentTab } from './tabs/EquipmentTab';
import { ProductsTab } from './tabs/ProductsTab';
import { OilsTab } from './tabs/OilsTab';
import { FurnitureTab } from './tabs/FurnitureTab';
import { AnimalsTab } from './tabs/AnimalsTab';
import { inventoryApi, useGetCharacterItemsQuery } from '../../entities/items/api/inventoryApi';
import { housesApi, useGetMyFurnitureQuery } from '../../entities/character/api/housesApi';
import { useGetMyResourcesQuery, resourcesApi } from '../../entities/resources/api/resourcesApi';
import { useDispatch } from 'react-redux';
import styles from "./InventoryModal.module.css";
import btn from '../../shared/styles/buttons.module.css';

const invalidateInventory = (d) => d(inventoryApi.util.invalidateTags(["Inventory"]));
const invalidateFurniture = (d) => {
  d(inventoryApi.util.invalidateTags(["Inventory"]));
  d(housesApi.util.invalidateTags(["HouseFurniture"]));
};

// Вкладка → какой api и какие теги инвалидировать
const TAB_INVALIDATE = {
  "Вещи":      invalidateInventory,
  "Рюкзак":    invalidateInventory,
  "Продукты":  invalidateInventory,
  "Мебель":    invalidateFurniture,
  "Животные":  invalidateInventory,
  "Масла":     invalidateInventory,
  "Ресурсы":   (d) => d(resourcesApi.util.invalidateTags(["Resources"])),
};


export const InventoryModal = ({ weight, maxWeight, onClose, setActiveModal, character, handleOpenMagic }) => {
  const firstTabs = [
    "Вещи",
    "Рюкзак",
    "Продукты",
    "Мебель",
    "Животные",
    "Ресурсы",
  ];

  const secondTabs = [
     `Вес: ${weight}/${maxWeight}`,
      "Параметры",
      "Магия",
      "Масла",
      "Подарки"
  ]

  const [activeTab, setActiveTab] = useState("Вещи");  

  const dispatch = useDispatch();
  // Синхронизация кеша при открытии модалки:
  // актуально, если предметы перемещали в другой вкладке браузера
  useEffect(() => {
    dispatch(inventoryApi.util.invalidateTags(["Inventory"]));
    dispatch(housesApi.util.invalidateTags(["HouseFurniture"]));
  }, [dispatch]);
  const { data: resources = [] } = useGetMyResourcesQuery();
    // Прелоад вкладок "Вещи" и "Мебель" — чтобы к моменту клика данные уже были в кеше
  useGetCharacterItemsQuery();
  useGetMyFurnitureQuery();
  

  const preloadAndSwitchTab = async (tab) => {
    if (tab === "Магия") {
      if (handleOpenMagic) {
        await handleOpenMagic();
      } else {
        setActiveModal('MAGIC_MODAL');
      }
      return;
    }

    // Повторный клик по активной вкладке → принудительное обновление
    if (activeTab === tab) {
      TAB_INVALIDATE[tab]?.(dispatch);
      return;
    }

    setActiveTab(tab);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.tabsAndCloseButton}>
            <div className={btn.tabGroup}>
              {firstTabs.map((tab, idx) => (
                <React.Fragment key={tab}>
                  <button
                    className={`${btn.textTab} ${activeTab === tab ? btn.textTabActive : ''}`}
                    onClick={() => preloadAndSwitchTab(tab)}                  
                  >
                    {tab}
                  </button>
                  {idx < firstTabs.length - 1 && <span className={styles.dot}>•</span>}
                </React.Fragment>
              ))}
            </div>
            <button className={styles.closeButton} onClick={onClose}>✕</button>
          </div>

          <div className={`${btn.tabGroup} ${btn.tabGroupSecond}`}>
            {secondTabs.map((tab, idx) => {
              const isWeightTab = tab.startsWith("Вес:");

              return (
                <React.Fragment key={tab}>
                  <button
                    className={
                      isWeightTab
                        ? `${btn.textTab} ${btn.textTabInfo}`
                        : `${btn.textTab} ${activeTab === tab ? btn.textTabActive : ""}`
                    }
                    onClick={isWeightTab ? undefined : () => preloadAndSwitchTab(tab)}                   
                  >
                    {tab}
                  </button>

                  {idx < secondTabs.length - 1 && <span className={styles.dot}>•</span>}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        <div className={styles.tabContent}>
          {activeTab === "Вещи" && <EquipmentTab character={character} />}
          {activeTab === "Продукты" && <ProductsTab character={character} />}
          {activeTab === "Масла" && <OilsTab character={character} />}
          {activeTab === "Мебель" && <FurnitureTab character={character} />}
          {activeTab === "Животные" && <AnimalsTab character={character} />}
          {activeTab === "Ресурсы" && resources && <ResourceBackpackComponent resources={resources}/>}
        </div>     
      </div>
    </div>
  );
};
import React, { useState, useRef, useEffect } from "react";
import { useDispatch } from 'react-redux';
import { mailApi } from "../../entities/mail/api/mailApi";
import { WriteMailTab } from "./tabs/WriteMailTab";
import { FriendsEnemiesTab } from "./tabs/FriendsEnemiesTab";
import { CategoriesTab } from "./tabs/CategoriesTab";
import {
  useGetMyCategoriesQuery,
  useGetCategoryDetailsQuery,
  useGetCategoryCharactersQuery,
  useCreateCategoryMutation,
  useDeleteCategoryMutation,
  useAddCharacterMutation,
  useRemoveCharacterMutation,
  useUpdateCategoryCheckboxesMutation,
} from "../../entities/mail/api/categoryApi";
import styles from "./FriendsModal.module.css";
import btn from '../../shared/styles/buttons.module.css';

export const FriendsModal = ({ onClose, doNotReceive, setDoNotReceive }) => {
  const dispatch = useDispatch();
  const tabs = ["Написать письмо", "Друзья/Враги", "Категории"];
  const [activeTab, setActiveTab] = useState(tabs[0]); 

  // Данные для вкладок 
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [showOnlineOnly, setShowOnlineOnly] = useState(false);  

  // Добавление/удаление персонажей
  const [addName, setAddName] = useState("");
  const [addCategoryId, setAddCategoryId] = useState("");
  const [addError, setAddError] = useState("");
  const [successMessage, setSuccessMessage] = useState(""); 
  const pendingFriendsSuccessRef = useRef(null);
  const pendingCategorySuccessRef = useRef(null);
  const [successKey, setSuccessKey] = useState(0);
  const [categorySuccessKey, setCategorySuccessKey] = useState(0);

  // Создание категории
  const [newCategoryName, setNewCategoryName] = useState("");
  const [categoryError, setCategoryError] = useState("");
  const [categorySuccess, setCategorySuccess] = useState("");  

  const [checkboxError, setCheckboxError] = useState(""); 

    // Стало (добавляем isLoading для форм):
  const [addCharacterMutation, { isLoading: isAdding }] = useAddCharacterMutation();
  const [removeCharacterMutation] = useRemoveCharacterMutation();
  const [createCategoryMutation, { isLoading: isCreating }] = useCreateCategoryMutation();
  const [deleteCategoryMutation] = useDeleteCategoryMutation();
  const [updateCheckboxesMutation] = useUpdateCategoryCheckboxesMutation();

  // Добавляем состояния для точечной блокировки кнопок в списках
  const [removingCharacterId, setRemovingCharacterId] = useState(null);
  const [deletingCategoryId, setDeletingCategoryId] = useState(null);
  const [updatingCheckboxId, setUpdatingCheckboxId] = useState(null);


  // -------------------------
  // Функции загрузки данных
  // -------------------------

  const { 
    data: myCategoriesData,    
    refetch: refetchCategories 
  } = useGetMyCategoriesQuery();
  
  const { 
    data: detailedCategoriesData,     
    refetch: refetchDetails 
  } = useGetCategoryDetailsQuery();
  
  const { 
    data: charactersData,     
    refetch: refetchCharacters 
  } = useGetCategoryCharactersQuery(
    { categoryId: selectedCategoryId, isOnline: showOnlineOnly },
    { skip: !selectedCategoryId }
  );


  // Автоматическая установка ID первой категории при загрузке
  useEffect(() => {
    if (myCategoriesData && myCategoriesData.length > 0) {
      if (!selectedCategoryId) setSelectedCategoryId(myCategoriesData[0].id);
      if (!addCategoryId) setAddCategoryId(myCategoriesData[0].id);
    }
  }, [myCategoriesData, selectedCategoryId, addCategoryId]);



  // -------------------------
  // Добавление / удаление персонажей
  // -------------------------

  useEffect(() => {
    if (!pendingFriendsSuccessRef.current) return;
    setSuccessMessage(pendingFriendsSuccessRef.current);
    setSuccessKey(k => k + 1);
    setAddError("");
    pendingFriendsSuccessRef.current = null;
  }, [charactersData]);
  
  useEffect(() => {
  if (!pendingCategorySuccessRef.current) return;
  setCategorySuccess(pendingCategorySuccessRef.current);
  setCategorySuccessKey(k => k + 1);
  setCategoryError("");
  pendingCategorySuccessRef.current = null;
}, [detailedCategoriesData]);

const handleAddCharacter = async () => {   
  if (!addName.trim()) {
    setSuccessMessage("");
    return setAddError("Введите ник персонажа");
  }
  if (!addCategoryId) {
    setSuccessMessage("");
    return setAddError("Выберите категорию");
  }

  try {
    await addCharacterMutation({ categoryId: addCategoryId, characterName: addName.trim() }).unwrap();
    pendingFriendsSuccessRef.current = "Персонаж добавлен";
    setAddName("");
  } catch (err) {
    setSuccessMessage("");
    if (err.status === 404) setAddError("Персонажа с таким ником не существует");
    else if (err.status === 400) setAddError("Достигнут лимит персонажей");
    else if (err.status === 409) setAddError("Персонаж уже есть в этой категории");
    else setAddError("Ошибка при добавлении персонажа");
  }
};

const handleRemoveCharacter = async (characterId) => {
  if (!selectedCategoryId) return;
  if (removingCharacterId === characterId) return; 
  setRemovingCharacterId(characterId); 
  try {
    await removeCharacterMutation({ categoryId: selectedCategoryId, characterId }).unwrap();
  } catch (err) {
    console.error("Ошибка удаления персонажа:", err);
  } finally {
    setRemovingCharacterId(null);
  }
};

const handleCreateCategory = async () => {    
  if (!newCategoryName.trim()) {
    setCategorySuccess("");   // ← сюда (перед ошибкой валидации)
    return setCategoryError("Введите название");
  }

  try {
    await createCategoryMutation({ name: newCategoryName.trim() }).unwrap();
    pendingCategorySuccessRef.current = "Категория добавлена"; 
    setNewCategoryName("");
  } catch (err) {
    setCategorySuccess("");
    if (err.status === 409) setCategoryError("У вас уже есть категория с таким названием");
    else setCategoryError("Не удалось создать категорию");
  }
};

const handleDeleteCategory = async (categoryId) => {
  if (deletingCategoryId === categoryId) return;
  setDeletingCategoryId(categoryId);
  try {
    await deleteCategoryMutation(categoryId).unwrap();
  } catch (err) {
    console.error("Ошибка удаления категории:", err);
  } finally {
    setDeletingCategoryId(null);
  }
};

const handleCategoryCheckboxChange = async (categoryId, field, value) => {
  const category = detailedCategoriesData?.find(c => c.id === categoryId);
  if (!category) return;
  if (updatingCheckboxId === categoryId) return; 

  setUpdatingCheckboxId(categoryId);
  try {
    await updateCheckboxesMutation({
      categoryId,
      data: {
        is_send_notifications: category.is_send_notifications,
        is_receive_notifications: category.is_receive_notifications,
        is_block_send_mails: category.is_block_send_mails,
        [field]: value,
      }
    }).unwrap();
  } catch {
    setCheckboxError("Не удалось обновить настройки");
  } finally {
    setUpdatingCheckboxId(null); 
  }
};

// Упростите переключение вкладок (RTK Query сам работает с кэшем)
const handleTabClick = async (tab) => { 

  // Если кликнули на активную вкладку - обновляем данные
  if (activeTab === tab) {
    try {
      if (tab === "Друзья/Враги") {
        await Promise.all([refetchCategories(), refetchCharacters()]);
        // Очищаем поля при обновлении
        setAddName("");
        setAddError("");
        setSuccessMessage("");
      } else if (tab === "Категории") {
        await refetchDetails();
        // Очищаем поля при обновлении
        setNewCategoryName("");
        setCategoryError("");
        setCategorySuccess("");
      } else if (tab === "Написать письмо") {
        dispatch(mailApi.util.invalidateTags(['MailSettings']));
      }
    } catch (err) {
      console.error("Ошибка обновления вкладки:", err);
    }
    return;
  }

  // Переключение на другую вкладку
  if (tab === "Друзья/Враги") {
    setAddName("");
    setAddError("");
    setSuccessMessage("");
  } else if (tab === "Категории") {
    setNewCategoryName("");
    setCategoryError("");
    setCategorySuccess("");
  }
  setActiveTab(tab);
};

  // -------------------------
  // Эффекты для автоочистки сообщений
  // -------------------------
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, successKey]); 

  useEffect(() => {
    if (categorySuccess) {
      const timer = setTimeout(() => setCategorySuccess(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [categorySuccess, categorySuccessKey]);

  useEffect(() => {
    if (checkboxError) {
      const timer = setTimeout(() => setCheckboxError(""), 5000);
      return () => clearTimeout(timer);
    }
} , [checkboxError]);

  // -------------------------
  // JSX
  // -------------------------
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.tabsAndCloseButton}>
            <div className={btn.tabGroup}>
              {tabs.map((tab, index) => (
                <React.Fragment key={tab}>
                  <button
                    className={`${btn.textTab} ${activeTab === tab ? btn.textTabActive : ""}`}
                    onClick={() => handleTabClick(tab)}                    
                  >
                    {tab}
                  </button>
                  {index < tabs.length - 1 && <span className={styles.dot}>•</span>}
                </React.Fragment>
              ))}
            </div>
            <button className={styles.closeButton} onClick={onClose}>✕</button>
          </div>
        </div>

        <div className={styles.tabContent}>
          {activeTab === "Написать письмо" && (
            <WriteMailTab              
              doNotReceive={doNotReceive}
              setDoNotReceive={setDoNotReceive}
            />
          )}
          {activeTab === "Друзья/Враги" && (
            <FriendsEnemiesTab
              categories={myCategoriesData || []}
              selectedCategoryId={selectedCategoryId}
              setSelectedCategoryId={setSelectedCategoryId}
              showOnlineOnly={showOnlineOnly}
              setShowOnlineOnly={setShowOnlineOnly}        
              characters={charactersData?.characters || []}
              addName={addName}
              setAddName={setAddName}
              addCategoryId={addCategoryId}
              setAddCategoryId={setAddCategoryId}
              addError={addError}
              successMessage={successMessage}              
              handleAdd={handleAddCharacter}
              isAdding={isAdding}
              handleRemove={handleRemoveCharacter}
              removingCharacterId={removingCharacterId}     
            />
          )}
          {activeTab === "Категории" && (
            <CategoriesTab
              detailedCategories={detailedCategoriesData || []}
              newCategoryName={newCategoryName}
              setNewCategoryName={setNewCategoryName}              
              categoryError={categoryError}
              categorySuccess={categorySuccess}
              onCreate={handleCreateCategory}
              isCreating={isCreating}
              onDelete={handleDeleteCategory}
              deletingCategoryId={deletingCategoryId}
              onCheckboxChange={handleCategoryCheckboxChange}   
              updatingCheckboxId={updatingCheckboxId}           
              checkboxError={checkboxError}               
            />
          )}
        </div>
      </div>
    </div>
  );
};
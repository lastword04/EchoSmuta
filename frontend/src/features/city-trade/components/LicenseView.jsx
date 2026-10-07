// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useEffect, useRef, useCallback } from "react";
import {
  useCreateCityShopMutation,
  useRenewCityShopLicenseMutation,
  useLevelUpCityShopMutation,
  useUpdateCityShopInfoMutation,
  useUpdateCityShopPhotoMutation,
} from "../../../entities/items/api/inventoryApi";
import { useUploadFileMutation } from "../../../entities/file/api/fileApi";
import { config } from "../../../shared/config/env/env";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import { formatLicenseTime } from '../utils/dateFormatter';
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import ShopPurchaseView from "./ShopPurchaseView";
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from "./LicenseView.module.css";
import btn from '../../../shared/styles/buttons.module.css';



// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function LicenseView({ 
  initialShopData, 
  initialHasShop, 
  locationSlug, 
  shopType, 
  onRefresh  
}) {
  
  // ── Конфигурация ──
  const locationConfig = getTradeLocationConfig(locationSlug);

  // ── Hooks ──
  const { currentError, showError } = useErrorToast();
  const [createShop] = useCreateCityShopMutation();
  const [renewLicense] = useRenewCityShopLicenseMutation();
  const [levelUpShop] = useLevelUpCityShopMutation();
  const [updateInfo] = useUpdateCityShopInfoMutation();
  const [updatePhoto] = useUpdateCityShopPhotoMutation();
  const [uploadFile] = useUploadFileMutation();

  // ── Refs ──
  const isMountedRef = useRef(true);

  // ── State ──
  const [shopData, setShopData] = useState(initialShopData);
  const [hasShop, setHasShop] = useState(initialHasShop);
  const [shopName, setShopName] = useState(initialShopData?.shop?.name || locationConfig?.shopType || "Лавка");
  const [shopDescription, setShopDescription] = useState(initialShopData?.shop?.description || "");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isExtending, setIsExtending] = useState(false);
  const [isLevelingUp, setIsLevelingUp] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);

  // ── Effects ──

  // Данные лавки — синхронизируем всегда (это не форма)
useEffect(() => {
    setShopData(initialShopData);
    setHasShop(initialHasShop);    
}, [initialShopData, initialHasShop]);

// Поля формы и файл — только при смене локации/появлении лавки,
// НЕ при каждом фоновом рефете (иначе стирается редактирование)
useEffect(() => {
    setShopName(initialShopData?.shop?.name || locationConfig?.shopType || "Лавка");
    setShopDescription(initialShopData?.shop?.description || "");
    setSelectedFile(null);
    setPreviewUrl(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
}, [locationSlug, initialHasShop]);

  // Очищаем blob URL при изменении previewUrl и при unmount
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Отслеживаем unmount компонента
  useEffect(() => {
    isMountedRef.current = true;
    return () => { 
      isMountedRef.current = false; 
    };
  }, []);

  // ── Callbacks ──

  const handlePurchaseShop = useCallback(async () => {
    if (isPurchasing) return;
    setIsPurchasing(true);
    try {
      await createShop({ locationSlug }).unwrap();
      await onRefresh?.();
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = 'Произошла ошибка при покупке';
      if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_LEVEL_FOR_CITY_TRADE_SHOP') {
        const requiredLevel = errorData.extras?.required_level || '?';
        errorMessage = `Недостаточный уровень. Требуется ${requiredLevel} уровень.`;
      } else if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP') {
        const required = errorData.extras?.required_ducats || '?';
        errorMessage = `Недостаточно средств. Требуется ${required} дт.`;
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setIsPurchasing(false);
    }
  }, [isPurchasing, createShop, onRefresh, showError, locationSlug]);

  const handleFileChange = useCallback((e) => {
    const file = e.target.files[0];    
    if (file) {
      setSelectedFile(file);
      if (previewUrl && previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(file));
    }
  }, [previewUrl]);

  const handleExtendLicense = useCallback(async () => {
    if (isExtending) return;
    setIsExtending(true);
    try {
      const shopId = shopData?.shop?.id;
      if (!shopId) { showError('Не удалось определить ID магазина'); return; }
      const updatedShop = await renewLicense({ shopId, locationSlug }).unwrap();
      setShopData({ ...shopData, shop: updatedShop });
      await onRefresh?.();
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = 'Произошла ошибка при продлении лицензии';
      if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP') {
        errorMessage = `Недостаточно средств. Требуется: ${errorData.extras?.required_ducats || '?'} дт.`;
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setIsExtending(false);
    }
  }, [isExtending, shopData, renewLicense, onRefresh, showError, locationSlug]);

  const handleLevelUp = useCallback(async () => {
    if (isLevelingUp) return;
    setIsLevelingUp(true);
    try {
      const result = await levelUpShop({ locationSlug }).unwrap();
      setShopData({ shop: result.shop, settings: result.settings, photo: shopData.photo, sale_items: result.sale_items });
      await onRefresh?.();
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = 'Произошла ошибка при повышении уровня';
      if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP') {
        errorMessage = `Недостаточно средств. Требуется: ${errorData.extras?.required_ducats || '?'} дт.`;
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setIsLevelingUp(false);
    }
  }, [isLevelingUp, levelUpShop, shopData, onRefresh, showError, locationSlug]);

  const handleUploadPhoto = useCallback(async () => {    
    if (isUploading) return;
    if (!selectedFile) { showError('Файл не выбран'); return; }
    const allowedFormats = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedFormats.includes(selectedFile.type)) {
        showError('Неверный формат файла. Допустимые форматы: JPEG, JPG, PNG, GIF');
        return;
    }
    const shopId = shopData?.shop?.id;
    if (!shopId) { showError('Не удалось определить ID магазина'); return; }  // ← проверка ДО включения флага

    setIsUploading(true);
    try {
      const uploadedFile = await uploadFile({ file: selectedFile }).unwrap();
        if (!isMountedRef.current) return;
        const updatedShop = await updatePhoto({ shopId, photoId: uploadedFile.id, locationSlug }).unwrap();
        if (!isMountedRef.current) return;
        setShopData({ ...shopData, shop: updatedShop, photo: uploadedFile });
        setPreviewUrl(null);
        setSelectedFile(null);
        await onRefresh?.();
    } catch (error) {
        if (!isMountedRef.current) return;
        showError(error?.data?.detail || 'Произошла ошибка при загрузке файла');
    } finally {
        if (isMountedRef.current) setIsUploading(false);  // ← разблокировка ГАРАНТИРОВАНА
    }
}, [isUploading, selectedFile, shopData, updatePhoto, uploadFile, onRefresh, showError, locationSlug]);

  const handleDeletePhoto = useCallback(async () => {
    if (isDeleting) return;
    setIsDeleting(true);
    try {
      const shopId = shopData?.shop?.id;
      if (!shopId) { showError('Не удалось определить ID магазина'); return; }
      const updatedShop = await updatePhoto({ shopId, photoId: null, locationSlug }).unwrap();
      setShopData({ ...shopData, shop: updatedShop, photo: null });
      setPreviewUrl(null);
      setSelectedFile(null);
      await onRefresh?.();
    } catch (error) {
      const errorData = error?.data;
      showError(errorData?.detail || 'Произошла ошибка при удалении файла');
    } finally {
      setIsDeleting(false);
    }
  }, [isDeleting, shopData, updatePhoto, onRefresh, showError, locationSlug]);

  const handleSave = useCallback(async () => {
    if (isSaving) return;
    setIsSaving(true);
    try {
      const shopId = shopData?.shop?.id;
      if (!shopId) { showError('Не удалось определить ID магазина'); return; }
      const updatedShop = await updateInfo({ shopId, data: { name: shopName, description: shopDescription }, locationSlug }).unwrap();
      setShopData({ ...shopData, shop: updatedShop });
      await onRefresh?.();
    } catch (error) {
      const errorData = error?.data;
      showError(errorData?.detail || 'Произошла ошибка при сохранении');
    } finally {
      setIsSaving(false);
    }
  }, [isSaving, shopData, shopName, shopDescription, updateInfo, onRefresh, showError, locationSlug]);

  // ── Guards ──

  if (hasShop === false && locationConfig?.purchaseInfo) {
    return (
      <>
        <ErrorToast message={currentError} />
        <ShopPurchaseView 
          purchaseInfo={locationConfig.purchaseInfo} 
          onPurchase={handlePurchaseShop} 
          isPurchasing={isPurchasing} 
          locationSlug={locationSlug} 
        />
      </>
    );
  }

  if (!shopData) return null;

  // ── Derived ──
  const licenseExpired = shopData?.shop?.end_license ? parseUtcDate(shopData.shop.end_license) < Date.now() : true;
  const licenseTime = formatLicenseTime(shopData?.shop?.end_license);
  const licenseCost = 15;
  const licenseWeeks = 2;
  const shopLevel = shopData?.shop?.level || 0;
  const shopCapacity = shopData?.settings?.capacity || 0;
  const salesTax = shopData?.settings?.tax ? parseFloat((shopData.settings.tax * 100).toFixed(2)) : 0;
  const levelUpCost = shopData?.settings?.price_up_level;
  const shopNumber = shopData?.shop?.number || 0;
  const shopPhotoUrl = shopData?.photo?.id 
    ? `${config.FILE_API_BASE_URL}/${shopData.photo.id}/content?v=${shopData.photo.updated_at || shopData.shop?.updated_at || Date.now()}` 
    : null;

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.licenseContainer}>
      <div className={styles.borderBox}>
        <ErrorToast message={currentError} />
        <div className={styles.header}>
          <h2 className={styles.title}>{shopType} № {shopNumber}</h2>
        </div>
        <div className={styles.content}>
          {/* Секция лицензии */}
          <div className={styles.section}>
            <div className={styles.licenseStatus}>
              Лицензия: {licenseExpired 
                ? <span className={styles.expired}>Истек срок лицензии</span> 
                : <span className={styles.active}>Активна ({licenseTime})</span>}
            </div>
            <div className={styles.licenseCost}>Стоимость лицензии на {licenseWeeks} недели: {licenseCost} дт.</div>
            <button 
              className={`${btn.gameButton} ${btn.sizeLarge}`} 
              onClick={handleExtendLicense} 
              disabled={isExtending}
            >
              Продлить лицензию
            </button>
          </div>

          <div className={styles.divider}></div>

          {/* Секция характеристик магазина */}
          <div className={styles.section}>
            <div className={styles.infoRow}>
              <span>Уровень {locationConfig?.shopTypeGenitive || shopType.toLowerCase()}:</span>
              <span className={styles.value}>{shopLevel}</span>
            </div>
            <div className={styles.infoRow}>
              <span>Вместимость {locationConfig?.shopTypeGenitive || shopType.toLowerCase()}:</span>
              <span className={styles.value}>{shopCapacity}</span>
            </div>
            <div className={styles.infoRow}>
              <span>Налог с продажи:</span>
              <span className={styles.value}>{salesTax}%</span>
            </div>
            {levelUpCost !== null && (
              <>
                <div className={styles.levelUpInfo}>
                  Повысить уровень {locationConfig?.shopTypeGenitive || shopType.toLowerCase()} за <span className={styles.price}>{levelUpCost} дт.</span>
                </div>
                <button 
                  className={`${btn.gameButton} ${btn.sizeLarge}`} 
                  onClick={handleLevelUp} 
                  disabled={isLevelingUp}
                >
                  Повысить уровень
                </button>
              </>
            )}
          </div>

          <div className={styles.divider}></div>

          {/* Секция редактирования и логотипа */}
          <div className={styles.section}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Название {locationConfig?.shopTypeGenitive || shopType.toLowerCase()}:</label>
              <input 
                type="text" 
                value={shopName} 
                onChange={(e) => setShopName(e.target.value)} 
                maxLength={25} 
                className={styles.input} 
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Описание {locationConfig?.shopTypeGenitive || shopType.toLowerCase()}:</label>
              <textarea 
                value={shopDescription} 
                maxLength={75} 
                onChange={(e) => { if (e.target.value.length <= 75) setShopDescription(e.target.value); }} 
                onKeyDown={(e) => { if (e.key === "Enter") e.preventDefault(); }} 
                onPaste={(e) => { 
                  e.preventDefault(); 
                  const pastedText = e.clipboardData.getData('text/plain').replace(/\n/g, ''); 
                  const newValue = shopDescription + pastedText; 
                  setShopDescription(newValue.slice(0, 75)); 
                }} 
                className={styles.textarea} 
                rows={2} 
              />
            </div>
            <label className={styles.label}>Логотип (размер 120x90):</label>
            <div className={styles.bigGroup}>
              <div className={styles.firstGroup}>
                <span className={styles.fileName}>{selectedFile ? selectedFile.name : "Файл не выбран"}</span>
                <label htmlFor="logo-upload" className={`${btn.gameButton} ${btn.sizeFull} ${styles.centerLabel}`}>Выберите файл</label>
                <div className={styles.photoButtons}>
                  <button className={btn.gameButton} onClick={handleUploadPhoto} disabled={isUploading}>Загрузить</button>
                  {(previewUrl || shopPhotoUrl) && (
                    <button 
                      className={`${btn.gameButton} ${btn.colorDanger}`} 
                      onClick={handleDeletePhoto} 
                      disabled={isDeleting}
                    >
                      Удалить файл
                    </button>
                  )}
                </div>
              </div>
              <div className={styles.secondGroup}>
                <input 
                  type="file" 
                  accept="image/jpeg,image/jpg,image/png,image/gif" 
                  onChange={handleFileChange} 
                  className={styles.fileInput} 
                  id="logo-upload" 
                />
                <div className={styles.preview}>
                  <img
                    src={previewUrl || shopPhotoUrl || '/images/city-trade/no-image.png'}
                    alt="Preview"
                    className={styles.previewImage}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = '/images/city-trade/no-image.png';
                    }}
                  />
                </div>
              </div>
            </div>
            <div className={styles.saveButtonWrapper}>
              <button className={btn.accentButton} onClick={handleSave} disabled={isSaving}>Сохранить</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LicenseView;
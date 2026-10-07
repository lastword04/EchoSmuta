/**
 * ВАЖНО: Эта страница НЕ использует useLocationPageController!
 * 
 * Причина: CityTradeLocation имеет сложную навигацию:
 * - Физическая смена локации для мастерских (аптека → лаборатория)
 * - Два типа мастерских (production vs non-production)
 * - Суб-навигация внутри "Лицензии"
 * 
 * Слушает topBarActionsSlice напрямую для событий от TopBar,
 * но обрабатывает их через свой handleViewChange.
 */

import { useEffect, useLayoutEffect, useState, useCallback, useRef } from "react";
import { useSelector, useDispatch } from 'react-redux';
import { useViewEntryPrefetches } from '../../shared/hooks/location/useViewEntryPrefetches';
import { useCancelExpiredCraftingMutation, inventoryApi } from '../../entities/items/api/inventoryApi';
import { getTradeLocationConfig } from "../../shared/config/locations/tradeConfig";
import { getLocationTexts } from "./config/locationTextConfig";
import { useShopStatus } from '../../entities/items/hooks/useShopStatus';
import { clearLastCrafting } from './store/craftingSlice';
import { WORKSHOP_TO_PARENT_MAP, normalizeViewId, getInitialView } from '../../shared/config/locations/locationNavConfig';
import { useLocationNavigation } from '../../shared/hooks/location/useLocationNavigation';
import { consumeAction } from '../../shared/store/topBarActionsSlice';
import { useErrorToast } from "../../shared/hooks/ui/useErrorToast";
import { useRefreshCurrentView } from '../../shared/hooks/location/useRefreshCurrentView';

import LicenseView from "./components/LicenseViewContainer";
import RecipesView from "./components/RecipesView";
import MyRecipesView from "./components/MyRecipesView";
import MyShopView from "./components/MyShopView";
import ShopDetailView from "./components/ShopDetailView";
import WorkshopView from "./components/WorkshopView";
import ProductionLicenseView from "./components/ProductionLicenseView";
import ShopsListView from "./components/ShopsListView";
import SalesHistoryView from "./components/SalesHistoryView";
import ErrorToast from "../../shared/ui/ErrorToast/ErrorToast";
import { ErrorBoundary } from '../../shared/ui/ErrorBoundary/ErrorBoundary';

import styles from "./CityTradeLocation.module.css";
import btn from '../../shared/styles/buttons.module.css';


const WORKSHOP_VIEWS = ["licenses", "workshop", "recipes", "your-recipes", "sales-history"];
const SUBNAV_VIEWS = ["licenses", "recipes", "your-recipes", "sales-history"];

function CityTradeLocation({ character, onRefresh, handleLocationChange }) {
    const dispatch = useDispatch();
    
    const { navigation, select } = useLocationNavigation();
    const { currentError, showError } = useErrorToast();
    const { hasShop } = useShopStatus(character?.location_slug);

    // --- RTK Query mutations ---
    const [cancelExpiredCrafting] = useCancelExpiredCraftingMutation();

    // --- Redux state ---
    const lastAction = useSelector(state => state.topBarActions?.lastAction);
    const lastCraftingId = useSelector(state => state.session?.crafting?.lastCraftingId);
    const savedWorkshopLocationSlug = useSelector(state => state.session?.crafting?.workshopLocationSlug);

    // --- Local state ---
    const [isNavLoading, setIsNavLoading] = useState(false);
    const [isSubNavLoading, setIsSubNavLoading] = useState(false);
    const [selectedShopId, setSelectedShopId] = useState(null);    
    const [initialShopData, setInitialShopData] = useState(null);

    // --- Refs ---
    const lastRenderedLocationSlugRef = useRef(null);
    const activeViewRef = useRef(null);

    // --- Derived values ---
    const locationSlug = character?.location_slug;

    const getLocationConfig = useCallback(() => {
        if (!character) return null;
        const currentSlug = character.location_slug;
        let config = getTradeLocationConfig(currentSlug);
        if (!config) {
            const parentConfig = Object.entries(WORKSHOP_TO_PARENT_MAP).find(
                ([, parentSlug]) => getTradeLocationConfig(parentSlug)?.workshopLocationSlug === currentSlug
            );
            if (parentConfig) config = getTradeLocationConfig(parentConfig[1]);
        }
        return config;
    }, [character]);

    const getParentLocationSlug = useCallback(() => {
        if (!character) return null;
        const currentSlug = character.location_slug;
        const config = getTradeLocationConfig(currentSlug);
        if (config) return currentSlug;
        return WORKSHOP_TO_PARENT_MAP[currentSlug] || currentSlug;
    }, [character]);    

    const locationConfig = getLocationConfig();
    const parentLocationSlug = getParentLocationSlug();
    const texts = getLocationTexts(parentLocationSlug);    

    const activeView = navigation?.activeView ? normalizeViewId(navigation.activeView) : getInitialView(locationSlug);
    const setActiveView = (viewId) => select(viewId);

    const showSubNav = hasShop && (activeView === "licenses" || activeView === "recipes" || activeView === "your-recipes" || activeView === "sales-history");
    const showSalesHistoryTab = hasShop && !locationConfig?.isProduction;

    const { requestView } = useViewEntryPrefetches(locationSlug, character?.id);
    const refreshCurrentView = useRefreshCurrentView(locationSlug, character?.id, inventoryApi);

    // --- Cancel expired crafting on server ---
    useEffect(() => {
        const cancelCraftingOnServer = async () => {
            try {
                await cancelExpiredCrafting().unwrap();
            } catch (error) {
                console.error('[CityTradeLocation] Failed to cancel crafting on server:', error);
            }
        };

        if (lastCraftingId && savedWorkshopLocationSlug && character?.location_slug) {
            if (character.location_slug !== savedWorkshopLocationSlug) {
                dispatch(clearLastCrafting());
                cancelCraftingOnServer();
            }

            const isCurrentlyInWorkshop = Object.keys(WORKSHOP_TO_PARENT_MAP).includes(character.location_slug);
            const savedWasInWorkshop = Object.keys(WORKSHOP_TO_PARENT_MAP).includes(savedWorkshopLocationSlug);
            if (!isCurrentlyInWorkshop && savedWasInWorkshop) {
                dispatch(clearLastCrafting());
                cancelCraftingOnServer();
            }
        }

        if (character?.status === 'offline' && lastCraftingId) {
            dispatch(clearLastCrafting());
            cancelCraftingOnServer();
        }
    }, [character?.location_slug, character?.status, lastCraftingId, savedWorkshopLocationSlug, dispatch, cancelExpiredCrafting]);

    // --- Sync activeView to ref for use in effects ---
    useEffect(() => {
        activeViewRef.current = activeView;
    }, [activeView]);

    // --- Handle TopBar actions ---
    useEffect(() => {
        if (!lastAction || lastAction.consumed) return;
        if (lastAction.type !== 'TRADE_BUTTON_CLICK') return;
        if (lastAction.payload.locationSlug !== character?.location_slug) {
            dispatch(consumeAction());
            return;
        }

        const isSubNavActive = SUBNAV_VIEWS.includes(activeViewRef.current);
        const clickedSubNavButton = lastAction.payload.id === "licenses";

        if (isSubNavActive && clickedSubNavButton) {
            refreshCurrentView();
            dispatch(consumeAction());
            return;
        }

        handleViewChange(lastAction.payload.id);
        dispatch(consumeAction());
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lastAction, character?.location_slug, character?.id, refreshCurrentView]);

    // --- Reset view on location change (unless it's a workshop transition) ---
   useLayoutEffect(() => {
    const prevSlug = lastRenderedLocationSlugRef.current;
    const currentSlug = locationSlug;
    if (prevSlug === currentSlug) return;   

        const getRelatedLocationSlug = (slug) => {
            if (!slug) return null;
            const cfg = getTradeLocationConfig(slug);
            if (cfg?.workshopLocationSlug) return cfg.workshopLocationSlug;
            return WORKSHOP_TO_PARENT_MAP[slug] || null;
        };

        const isWorkshopTransition = prevSlug && prevSlug !== currentSlug && getRelatedLocationSlug(prevSlug) === currentSlug;
        if (!isWorkshopTransition) {
            const defaultView = getInitialView(locationSlug);
            select(defaultView);
        }
        lastRenderedLocationSlugRef.current = currentSlug;
    }, [locationSlug, select, dispatch]);

    

    

    // --- Handle view change (may involve physical location change for workshop transitions) ---
    const handleViewChange = useCallback(async (viewId) => {
        if (locationConfig?.isProduction && !WORKSHOP_VIEWS.includes(viewId)) return;
        if (isNavLoading) return;

        const targetView = normalizeViewId(viewId);
        const isSameView = activeView === targetView;

        if (isSameView) {
            refreshCurrentView();
            if (SUBNAV_VIEWS.includes(activeView)) {
                setIsSubNavLoading(true);
                setTimeout(() => setIsSubNavLoading(false), 300);
            }
            return;
        }

        setIsNavLoading(true);
        const previousView = activeView;
        const currentlyInWorkshop = activeView === "workshop";

        try {
            if (!hasShop && (targetView === "your-shop" || targetView === "shop-detail")) return;

            if (targetView === "licenses") {
                if (currentlyInWorkshop) {
                    await handleLocationChange(parentLocationSlug, { targetView });
                } else {
                    await requestView(targetView);
                }
            } else if (targetView === "workshop") {
                if (!hasShop) return;
                if (!currentlyInWorkshop) {
                    const parentConfig = getTradeLocationConfig(parentLocationSlug);
                    if (parentConfig?.workshopLocationSlug) {

                        // 1. ПРИНУДИТЕЛЬНО инвалидируем кэш ПЕРЕД монтированием компонента
                        dispatch(inventoryApi.util.invalidateTags([
                            'StartedCrafting',
                            'WorkshopRecipes',
                            'WorkshopStats',
                        ]));

                        await handleLocationChange(parentConfig.workshopLocationSlug, { targetView });
                    } else if (parentConfig?.isProduction) {
                        await requestView(targetView);
                    }
                }
            } else {
                if (currentlyInWorkshop) {
                    await handleLocationChange(parentLocationSlug, { targetView });
                } else {
                    await requestView(targetView);
                }
            }
        } catch (error) {
            console.error("Ошибка при смене локации:", error);
            select(previousView);
            showError("Не удалось перейти в другую локацию. Попробуйте ещё раз.");
        } finally {
            setIsNavLoading(false);
        }
    }, [locationConfig, isNavLoading, activeView, hasShop, parentLocationSlug, handleLocationChange, requestView, select, showError, refreshCurrentView]);

    const handleNavClick = async (viewId) => {
        if (isNavLoading) return;
        await handleViewChange(viewId);
    };

    const handleShopClick = (shopId, shopData = null) => {
        setSelectedShopId(shopId);
        setInitialShopData(shopData);
        setActiveView("shop-detail");
    };
    

    // --- Render content based on active view ---
    const renderContent = () => {
        if (activeView === "shop-detail" && selectedShopId) {
            return (
                <ErrorBoundary>
                    <ShopDetailView
                        key={selectedShopId}
                        shopId={selectedShopId}
                        locationSlug={parentLocationSlug}
                        character={character}
                        onBack={() => setActiveView("shops")}                       
                        initialShopData={initialShopData}
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "licenses") {
            if (locationConfig?.isProduction) {
                return (
                    <ErrorBoundary>
                        <ProductionLicenseView
                            key={parentLocationSlug}
                            locationSlug={parentLocationSlug}
                            config={locationConfig}                                               
                        />
                    </ErrorBoundary>
                );
            }
            return (
                <ErrorBoundary>
                    <LicenseView
                        key={parentLocationSlug}
                        locationSlug={parentLocationSlug}
                        shopType={locationConfig?.shopType || "Лавка"}                       
                        onRefresh={onRefresh}                        
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "your-shop") {
            return (
                <ErrorBoundary>
                    <MyShopView 
                        key={parentLocationSlug} 
                        locationSlug={parentLocationSlug} 
                        character={character}         
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "workshop") {
            return (
                <ErrorBoundary>
                    <WorkshopView
                        key={parentLocationSlug}
                        locationSlug={parentLocationSlug}
                        onRefresh={onRefresh}
                        character={character}
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "recipes") {
            return (
                <ErrorBoundary>
                    <RecipesView 
                        key={parentLocationSlug} 
                        locationSlug={parentLocationSlug} 
                        character={character}                                 
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "your-recipes") {
            return (
                <ErrorBoundary>
                    <MyRecipesView 
                        key={parentLocationSlug} 
                        locationSlug={parentLocationSlug} 
                        character={character}         
                    />
                </ErrorBoundary>
            );
        }
        if (activeView === "sales-history") {
            return (
                <ErrorBoundary>
                    <SalesHistoryView 
                        key={parentLocationSlug} 
                        locationSlug={parentLocationSlug}                      
                    />
                </ErrorBoundary>
            );
        }        
        return activeView ? (
            <ErrorBoundary>
                <ShopsListView
                    key={parentLocationSlug}
                    parentLocationSlug={parentLocationSlug}
                    onShopClick={handleShopClick}          
                />
            </ErrorBoundary>
        ) : null;
    };

    return (
        <div className={styles.wrapper}>
            <ErrorToast message={currentError} />
            <div className={styles.contentBox}>
                {showSubNav && (
                    <div className={styles.topNavigation}>
                        <button
                            className={`${btn.gameButton} ${activeView === 'licenses' ? btn.gameButtonActive : ''}`}
                            onClick={() => handleNavClick("licenses")}
                            disabled={isNavLoading || isSubNavLoading}
                        >
                            {locationConfig?.navLabels?.licenses || "Лицензии"}
                        </button>
                        <span className={styles.dot}>•</span>
                        <button
                            className={`${btn.gameButton} ${activeView === 'recipes' ? btn.gameButtonActive : ''}`}
                            onClick={() => handleNavClick("recipes")}
                            disabled={isNavLoading || isSubNavLoading}
                        >
                            {texts.buyTab}
                        </button>
                        <span className={styles.dot}>•</span>
                        <button
                            className={`${btn.gameButton} ${activeView === 'your-recipes' ? btn.gameButtonActive : ''}`}
                            onClick={() => handleNavClick("your-recipes")}
                            disabled={isNavLoading || isSubNavLoading}
                        >
                            {texts.yourTab}
                        </button>
                        {showSalesHistoryTab && (
                            <>
                                <span className={styles.dot}>•</span>
                                <button
                                    className={`${btn.gameButton} ${activeView === 'sales-history' ? btn.gameButtonActive : ''}`}
                                    onClick={() => handleNavClick("sales-history")}
                                    disabled={isNavLoading || isSubNavLoading}
                                >
                                    {texts.historyTab || "История продаж"}
                                </button>
                            </>
                        )}
                    </div>
                )}
                {renderContent()}
            </div>
        </div>
    );
}

export default CityTradeLocation;
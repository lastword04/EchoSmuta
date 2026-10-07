import { useCallback } from 'react';
import { useLocationPageController } from '../../shared/hooks/location/useLocationPageController';
import BuyoutTab from './components/BuyoutTab';
import ExchangeTab from './components/ExchangeTab';
import { useGetResourcesQuery, useGetLotsQuery } from '../../entities/economy/api/economyApi';
import styles from './index.module.css';
import { ErrorBoundary } from '../../shared/ui/ErrorBoundary/ErrorBoundary';

const PawnShopPage = ({ character, onRefresh }) => {    
  const { activeTab: activeView } = useLocationPageController(character);

  const { 
    data: resourcesData,   
    refetch: refetchResources,
  } = useGetResourcesQuery(undefined);
  const { 
    data: lotsData,    
    refetch: refetchLots,
  } = useGetLotsQuery(undefined);

  const resources = resourcesData || [];
  const lots = lotsData || [];
  

  const refreshShopData = useCallback(async () => {
    await Promise.all([refetchResources(), refetchLots()]);
  }, [refetchResources, refetchLots]);

 

  return (
    <div className={styles.wrapper}>
      <div className={styles.contentBox}>
        <div className={styles.contentArea}>
          {activeView === 'buyout' && (
            <ErrorBoundary>
              <BuyoutTab 
                resources={resources} 
                onRefresh={onRefresh} 
                onShopDataRefresh={refreshShopData}               
              />
            </ErrorBoundary>
          )}
          {activeView === 'exchange' && (
            <ErrorBoundary>
              <ExchangeTab
                resources={resources}
                lots={lots}
                characterId={character?.id}
                onRefresh={onRefresh}
                onShopDataRefresh={refreshShopData}
              />
            </ErrorBoundary>
          )}
        </div>
      </div>
    </div>
  );
};

export default PawnShopPage;
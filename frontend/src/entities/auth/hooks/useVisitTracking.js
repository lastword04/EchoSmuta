import { useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useLocation } from 'react-router-dom';
import visitService from '../../../shared/services/visitService';
import { setVisitLoading,
        setVisitSuccess,
        setVisitError,
        selectIsVisitInitialized,
 } from '../store/visitSlice';


const TRACKED_ROUTES = ['/', '/register', '/login', '/forum'];

export const useVisitTracking = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  const isInitialized = useSelector(selectIsVisitInitialized);

  const trackVisit = useCallback(async () => {
    try {
      dispatch(setVisitLoading());
      const visitData = await visitService.visit();
      dispatch(setVisitSuccess(visitData));

      console.log('Visit tracked successfully:', visitData);
    } catch (error) {
      dispatch(setVisitError(error.message));
      console.error('Failed to track visit:', error);
    }
  }, [dispatch]);

  useEffect(() => {
    // Проверяем, нужно ли отслеживать текущий роут
    const shouldTrack = TRACKED_ROUTES.some(route => 
      location.pathname === route || location.pathname.startsWith(route)
    );

    // Делаем запрос только если:
    // 1. Роут нужно отслеживать
    // 2. Запрос еще не был сделан
    if (shouldTrack && !isInitialized) {
      trackVisit();
    }
  }, [location.pathname, isInitialized, trackVisit]);

};

export default useVisitTracking;
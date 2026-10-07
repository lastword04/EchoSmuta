import { useSelector, useDispatch } from 'react-redux';
import { useCallback } from 'react';

import {
  startLocationChange,
  confirmLocation,
  failLocationChange,
  selectView,  
} from '../../store/locationNavigationSlice';

export const useLocationNavigation = () => {
  const dispatch = useDispatch();
  const navigation = useSelector(state => state.locationNavigation);

  const requestLocationChange = useCallback((targetSlug) => {
    const requestId = navigation.requestId + 1;
    dispatch(startLocationChange({ targetSlug, requestId }));
    return requestId;
  }, [dispatch, navigation.requestId]);

  const confirm = useCallback((requestId) => {
    dispatch(confirmLocation({ requestId }));
  }, [dispatch]);

  const fail = useCallback((requestId) => {
    dispatch(failLocationChange({ requestId }));
  }, [dispatch]);

  const select = useCallback((viewId) => {
    dispatch(selectView({ viewId }));
  }, [dispatch]);  

  return {
    navigation,
    requestLocationChange,
    confirm,
    fail,
    select,    
  };
};
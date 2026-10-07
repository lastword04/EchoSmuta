import { useState, useRef, useEffect, useCallback } from 'react';

export const useErrorToast = (duration = 3000) => {
  const [currentError, setCurrentError] = useState(null);
  const errorTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    };
  }, []);

  const showError = useCallback((message) => {
    setCurrentError(message);
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    errorTimerRef.current = setTimeout(() => setCurrentError(null), duration);
  }, [duration]);

  const hideError = useCallback(() => {
    setCurrentError(null);
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
  }, []);

  return { currentError, showError, hideError };
};
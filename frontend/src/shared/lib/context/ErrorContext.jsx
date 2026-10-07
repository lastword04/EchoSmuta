import { createContext, useContext, useState, useCallback, useRef } from 'react';

const ErrorContext = createContext(null);

export const ErrorProvider = ({ children }) => {
    const [currentError, setCurrentError] = useState(null);
    const errorTimerRef = useRef(null);

    const showError = useCallback((message, duration = 3000) => {
        setCurrentError(message);
        if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
        errorTimerRef.current = setTimeout(() => setCurrentError(null), duration);
    }, []);

    const hideError = useCallback(() => {
        setCurrentError(null);
        if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    }, []);

    return (
        <ErrorContext.Provider value={{ currentError, showError, hideError }}>
            {children}
        </ErrorContext.Provider>
    );
};

export const useErrorContext = () => {
    const context = useContext(ErrorContext);
    if (!context) {
        throw new Error('useErrorContext must be used within ErrorProvider');
    }
    return context;
};
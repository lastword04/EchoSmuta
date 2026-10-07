import useVisitTracking from '../../entities/auth/hooks/useVisitTracking';

export const VisitTracker = ({ children }) => {
    useVisitTracking();
  return children;
};
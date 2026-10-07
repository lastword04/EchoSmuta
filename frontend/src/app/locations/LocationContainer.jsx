import React from 'react';
import { LocationContext } from '../../shared/lib/context/locationContext';
import { getComponentForLocation } from './locationRegistry';
import { withBasePage } from '../providers/hoc/withBasePage';

function LocationContainerInner() {
  return null;
}

const LocationContainerWithPage = withBasePage(LocationContainerInner);

function LocationContainer() {
  return (
    <LocationContext.Provider value={getComponentForLocation}>
      <LocationContainerWithPage />
    </LocationContext.Provider>
  );
}

export default LocationContainer;
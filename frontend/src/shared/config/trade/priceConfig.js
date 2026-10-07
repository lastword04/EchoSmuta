export const MIN_PRICE_RATIO = 0.5;
export const getMinAllowedPrice = (basePrice) => 
  basePrice > 0 ? basePrice * MIN_PRICE_RATIO : 0;
import StationPage from "../../pages/station-page/StationPage";
import HospitalPage from "../../pages/hospital/HospitalPage";
import ResourcePage from "../../pages/resource/ResourcePage";
import CityTradeLocation from "../../features/city-trade/CityTradeLocation";
import PawnShopPage from "../../features/pawnshop";
import TradeHallPage from "../../features/trade-hall/TradeHallPage";
import TavernPage from "../../pages/tavern/TavernPage";
import InnPage from "../../pages/inn/InnPage";
import HousePage from "../../pages/houses/HousePage";

import { getLocationName, AVALON_NUMBER, NIGHBORHOOD_AVALON_NUMBER } from "../../shared/config/locations/locations";

/**
 * Реестр компонентов локаций.
 * Связывает slug локации с её React-компонентом и метаданными.
 */
export const LOCATION_COMPONENTS = {
  [`${AVALON_NUMBER}.17.station`]: {
    component: StationPage,
    title: 'Вокзал',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.10.hospital`]: {
    component: HospitalPage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.26.pawn-shop`]: {
    component: PawnShopPage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.21.furniture-shop`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.22.hunting-shop`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.24.bird-market`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.25.fish-shop`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.9.pharmacy`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.35.laboratory`]: {
    component: CityTradeLocation,
    title: 'Лаборатория',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.36.kitchen`]: {
    component: CityTradeLocation,
    title: 'Кухня',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.37.carpentry-workshop`]: {
    component: CityTradeLocation,
    title: 'Столярная мастерская',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.38.hunter-workshop`]: {
    component: CityTradeLocation,
    title: 'Мастерская охотника',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.39.incubator`]: {
    component: CityTradeLocation,
    title: 'Инкубатор',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.13.forge`]: {
  component: CityTradeLocation,
  title: (character) => getLocationName(character?.location_slug),
  city: 'Авалон'
  },
  [`${AVALON_NUMBER}.16.jewelers`]: {
    component: CityTradeLocation,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.27.trade-hall`]: {
    component: TradeHallPage,
    title: 'Торговая Палата',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.15.tavern`]: {
    component: TavernPage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.12.inn`]: {
    component: InnPage,
    title: 'Гостиница',
    city: 'Авалон'
  },
  [`${AVALON_NUMBER}.19.residential-area`]: {
    component: HousePage,
    title: 'Частные дома',
    city: 'Авалон'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.1.swamp`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.5.forest`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.4.lake`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.6.sands`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.3.mine`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
  [`${NIGHBORHOOD_AVALON_NUMBER}.2.shaft`]: {
    component: ResourcePage,
    title: (character) => getLocationName(character?.location_slug),
    city: 'Окрестности Авалона'
  },
};

/**
 * Получить конфигурацию компонента локации по slug.
 * @param {string} locationSlug - slug локации
 * @returns {object} - конфигурация с component, title, city
 */
export const getComponentForLocation = (locationSlug) => {
  return LOCATION_COMPONENTS[locationSlug] || LOCATION_COMPONENTS['1.17.station']; // default
};

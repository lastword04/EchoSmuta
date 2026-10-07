import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import DealsView from './DealsView';

// --- Мок useDealsLogic: значение подменяется в beforeEach через hoisted-объект ---
const logicMock = vi.hoisted(() => ({ value: null }));

vi.mock('./hooks/useDealsLogic', () => ({
  useDealsLogic: () => logicMock.value,
}));

// --- Моки дочерних компонентов: проверяем только логику/ветки DealsView ---
vi.mock('./deal-ui/DealBackpack', () => ({
  DealBackpack: () => <div data-testid="backpack" />,
}));
vi.mock('./deal-ui/PartnerSelection', () => ({
  PartnerSelection: () => <div data-testid="partner-selection" />,
}));
vi.mock('./deal-ui/CardOverlays', () => ({
  CardOverlays: () => <div data-testid="card-overlays" />,
}));
vi.mock('./deal-ui/DealOfferTable', () => ({
  DealOfferTable: () => <div data-testid="deal-offer-table" />,
}));

function makeLogic(overrides = {}) {
  const noop = () => {};
  return {
    isLoading: false,
    activeDeal: null,
    nearbyPartners: [],
    myItems: [],
    myResources: [],
    myDealItems: [],
    partnerDealItems: [],
    moneyInput: '',
    setMoneyInput: noop,
    selectedCurrency: 'ducats',
    setSelectedCurrency: noop,
    quantities: {},
    setQty: noop,
    getQty: () => 1,
    isProcessing: false,
    errorMessage: '',
    selectedItem: null,
    setSelectedItem: noop,
    selectedResource: null,
    selectedPartnerId: '',
    setSelectedPartnerId: noop,
    cachedPartnerName: '',
    hasGold: true,
    isInitiator: true,
    myOffer: null,
    partnerOffer: null,
    iConfirmed: false,
    partnerConfirmed: false,
    dealFinished: false,
    isEditable: false,
    leftDisabled: false,
    partnerId: null,
    partnerName: 'Партнёр',
    myTax: 0,
    openResource: noop,
    closeResource: noop,
    openDealItemCard: noop,
    handleSelectPartner: noop,
    handleAddMoney: noop,
    handleAddResource: noop,
    handleRemoveResource: noop,
    handleAddItem: noop,
    handleRemoveItem: noop,
    handleRemoveDucats: noop,
    handleRemoveGold: noop,
    handleConfirm: noop,
    handleCancel: noop,
    displayName: (it) => it?.item_snapshot?.name || 'Актив',
    isItemAsset: (it) => it?.asset_type === 'ITEM' || it?.asset_type === 'INVENTORY_ITEM',
    resFree: () => 0,
    ...overrides,
  };
}

function renderDealsView(logic) {
  logicMock.value = logic;
  return render(<DealsView character={{ id: 'c1' }} onRefresh={() => {}} />);
}

describe('DealsView', () => {
  beforeEach(() => {
    logicMock.value = null;
  });

  it('рендерит экран выбора партнёра когда activeDeal=null', () => {
    renderDealsView(makeLogic({ activeDeal: null }));
    expect(screen.getByTestId('backpack')).toBeInTheDocument();
    expect(screen.getByTestId('partner-selection')).toBeInTheDocument();
    expect(screen.queryByTestId('deal-offer-table')).toBeNull();
  });

  it('рендерит экран активной сделки когда activeDeal существует', () => {
    renderDealsView(makeLogic({ activeDeal: { id: 'd1' } }));
    expect(screen.getByTestId('backpack')).toBeInTheDocument();
    // DealOfferTable рендерится дважды: моя сторона + сторона партнёра
    expect(screen.getAllByTestId('deal-offer-table')).toHaveLength(2);
    expect(screen.queryByTestId('partner-selection')).toBeNull();
  });

  it('показывает статус "Вы подтвердили сделку" когда iConfirmed=true', () => {
    renderDealsView(makeLogic({ activeDeal: { id: 'd1' }, iConfirmed: true, myOffer: {} }));
    expect(screen.getByText('Вы подтвердили сделку')).toBeInTheDocument();
  });

  it('показывает статус "Партнер подтвердил сделку" когда partnerConfirmed=true', () => {
    renderDealsView(makeLogic({ activeDeal: { id: 'd1' }, partnerConfirmed: true, partnerOffer: {} }));
    expect(screen.getByText('Партнер подтвердил сделку')).toBeInTheDocument();
  });
});
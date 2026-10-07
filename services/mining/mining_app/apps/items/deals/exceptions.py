import uuid

from fastapi import status

from shared.exceptions import CoreException


class DealError(CoreException):
    pass


class DealNotFoundError(DealError):
    def __init__(self, deal_id: uuid.UUID) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "Deal not found", "DEAL_NOT_FOUND", extras={"deal_id": str(deal_id)})


class DealAccessDeniedError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "Only deal participants may perform this action", "DEAL_ACCESS_DENIED")


class DealProximityError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Both characters must be online in the same location", "DEAL_PROXIMITY_REQUIRED")


class DealStateError(DealError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, "DEAL_INVALID_STATE")


class DealSelfPartnerError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, "Cannot create a deal with yourself", "DEAL_SELF_PARTNER")


class DealGoldTradeDisabledError(DealError):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "Для торговли золотом нужна лицензия торговца",
            "DEAL_GOLD_TRADE_DISABLED",
        )


class DealAssetUnavailableError(DealError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, "DEAL_ASSET_UNAVAILABLE")


class DealCompletionError(DealError):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, "DEAL_COMPLETION_FAILED")

class DealBothSidesMoneyError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Only one side may offer money in a deal", "DEAL_BOTH_SIDES_MONEY")


class DealNotReadyError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Not all parties are ready for the deal", "DEAL_NOT_READY")


class DealPartnerOfflineError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Partner is offline", "DEAL_PARTNER_OFFLINE")


class DealPartnerDepartedError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Partner has left the location", "DEAL_PARTNER_DEPARTED")

class DealEmptyOfferError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Your offer is empty", "DEAL_EMPTY_OFFER")

class DealSelfWeightLimitError(DealError):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "У вас нет места в рюкзаке",
            "DEAL_SELF_WEIGHT_LIMIT",
        )


class DealPartnerWeightLimitError(DealError):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "У партнёра по сделке нет места в рюкзаке",
            "DEAL_PARTNER_WEIGHT_LIMIT",
        )

class DealInsufficientFundsError(DealError):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Недостаточно средств", "INSUFFICIENT_FUNDS")

class DealMixedOfferError(CoreException):
    def __init__(self, detail: str = "Одна сторона сделки может предлагать только деньги или только товары", error_code: str = "DEAL_MIXED_OFFER", extras: dict | None = None, headers: dict | None = None) -> None:
        if extras is None: extras = {}
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code, error_type="DealMixedOfferError", extras=extras, headers=headers)

class DealBothSidesGoodsError(CoreException):
    def __init__(self, detail: str = "Товары в сделку может добавлять только одна сторона", error_code: str = "DEAL_BOTH_SIDES_GOODS", extras: dict | None = None, headers: dict | None = None) -> None:
        if extras is None: extras = {}
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code, error_type="DealBothSidesGoodsError", extras=extras, headers=headers)

class DealNoMoneySideError(CoreException):
    def __init__(self, detail: str = "Одна из сторон должна добавить деньги в сделку", error_code: str = "DEAL_NO_MONEY_SIDE", extras: dict | None = None, headers: dict | None = None) -> None:
        if extras is None: extras = {}
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code, error_type="DealNoMoneySideError", extras=extras, headers=headers)

class DealPriceTooLowError(CoreException):
    def __init__(self, detail: str = "Цена ниже половины стоимости товаров", error_code: str = "DEAL_PRICE_TOO_LOW", extras: dict | None = None, headers: dict | None = None) -> None:
        if extras is None: extras = {}
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code, error_type="DealPriceTooLowError", extras=extras, headers=headers)

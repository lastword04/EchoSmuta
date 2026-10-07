"""Экономика: дукаты, золото, переводы между персонажами."""
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema
from shared.schemas.characters import DucatsStat

from ....core.db import Session
from ....core.depends import get_service_token_payload, get_user_token_payload
from ..models import Character, CharacterCurrencyOperation
from ..schemas import (
    CharacterTransferRequestSchema, TransferResult,
    TransferValueCharactersSettingsReadSchema, CharacterDucatsBalanceResponse,
    CharacterDucatsOperationRequest, CharacterDucatsOperationResponse,
    CharacterCurrencyOperationRequest, CharacterCurrencyOperationResponse,
)
from ..use_cases.economy.transfer_value_characters import TransferValueCharacterUseCaseProtocol
from ..use_cases.economy.get_transfer_rules import GetTransferValueCharactersSettingsUseCaseProtocol
from ..use_cases.characters.update_ducats import UpdateCharacterDucatsUseCaseProtocol
from ..deps import (
    get_transfer_value_character_use_case,
    get_transfer_rules_use_case,
    get_character_update_ducats_use_case,
)

router = APIRouter()


@router.get('/internal/characters/{character_id}/ducats', response_model=CharacterDucatsBalanceResponse)
async def get_character_ducats(
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterDucatsBalanceResponse:
    character = await session.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found')

    return CharacterDucatsBalanceResponse(character_id=character.id, ducats=Decimal(str(character.ducats)))


async def _change_character_currency(
    session: Session,
    character_id: uuid.UUID,
    currency: str,
    data: CharacterCurrencyOperationRequest,
    operation_type: str
) -> CharacterCurrencyOperationResponse:
    existing_operation = await session.scalar(
        select(CharacterCurrencyOperation).where(CharacterCurrencyOperation.operation_id == data.operation_id)
    )
    if existing_operation is not None:
        return CharacterCurrencyOperationResponse(
            character_id=existing_operation.character_id,
            operation_id=existing_operation.operation_id,
            amount=existing_operation.amount,
            operation_type=existing_operation.operation_type,
            currency=existing_operation.currency,
            balance_after=existing_operation.balance_after
        )

    character = await session.scalar(
        select(Character).where(Character.id == character_id).with_for_update()
    )
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found')

    current_balance = getattr(character, currency)
    if not isinstance(current_balance, Decimal):
        current_balance = Decimal(str(current_balance))
    if operation_type == 'debit':
        balance_after = current_balance - data.amount
        if balance_after < 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Insufficient {currency}')
    else:
        balance_after = current_balance + data.amount

    setattr(character, currency, balance_after)

    operation = CharacterCurrencyOperation(
        operation_id=data.operation_id,
        character_id=character.id,
        currency=currency,
        operation_type=data.operation_type or operation_type,
        amount=data.amount,
        balance_after=balance_after,
        source=data.source,
        counterparty_id=data.counterparty_id,
        item_meta=data.item_meta,
        meta=data.meta,
    )
    session.add(operation)
    await session.commit()

    return CharacterCurrencyOperationResponse(
        character_id=character.id,
        operation_id=operation.operation_id,
        amount=operation.amount,
        operation_type=operation.operation_type,
        currency=operation.currency,
        balance_after=operation.balance_after
    )


async def _change_character_ducats(
    session: Session,
    character_id: uuid.UUID,
    data: CharacterDucatsOperationRequest,
    operation_type: str
) -> CharacterDucatsOperationResponse:
    existing_operation = await session.scalar(
        select(CharacterCurrencyOperation).where(CharacterCurrencyOperation.operation_id == data.operation_id)
    )
    if existing_operation is not None:
        return CharacterDucatsOperationResponse(
            character_id=existing_operation.character_id,
            operation_id=existing_operation.operation_id,
            amount=existing_operation.amount,
            operation_type=existing_operation.operation_type,
            ducats=existing_operation.balance_after
        )

    character = await session.scalar(
        select(Character).where(Character.id == character_id).with_for_update()
    )
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Character not found')

    current_balance = Decimal(str(character.ducats))

    if operation_type == 'debit':
        balance_after = current_balance - data.amount
        if balance_after < 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Insufficient ducats')
    else:
        balance_after = current_balance + data.amount

    character.ducats = balance_after

    operation = CharacterCurrencyOperation(
        operation_id=data.operation_id,
        character_id=character.id,
        currency='ducats',
        operation_type=operation_type,
        amount=data.amount,
        balance_after=balance_after
    )
    session.add(operation)
    await session.commit()

    return CharacterDucatsOperationResponse(
        character_id=character.id,
        operation_id=operation.operation_id,
        amount=operation.amount,
        operation_type=operation.operation_type,
        ducats=operation.balance_after
    )


@router.post('/internal/characters/{character_id}/ducats/debit', response_model=CharacterCurrencyOperationResponse)
async def debit_character_ducats(
    data: CharacterCurrencyOperationRequest,
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterCurrencyOperationResponse:
    return await _change_character_currency(session, character_id, 'ducats', data, 'debit')


@router.post('/internal/characters/{character_id}/ducats/credit', response_model=CharacterCurrencyOperationResponse)
async def credit_character_ducats(
    data: CharacterCurrencyOperationRequest,
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterCurrencyOperationResponse:
    return await _change_character_currency(session, character_id, 'ducats', data, 'credit')


@router.post('/internal/characters/{character_id}/gold/debit', response_model=CharacterCurrencyOperationResponse)
async def debit_character_gold(
    data: CharacterCurrencyOperationRequest,
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterCurrencyOperationResponse:
    return await _change_character_currency(session, character_id, 'gold', data, 'debit')


@router.post('/internal/characters/{character_id}/gold/credit', response_model=CharacterCurrencyOperationResponse)
async def credit_character_gold(
    data: CharacterCurrencyOperationRequest,
    session: Session,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload)
) -> CharacterCurrencyOperationResponse:
    return await _change_character_currency(session, character_id, 'gold', data, 'credit')


@router.post('/transfer', response_model=TransferResult, status_code=200)
async def transfer_value_character(
    character: CharacterTransferRequestSchema,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: TransferValueCharacterUseCaseProtocol = Depends(get_transfer_value_character_use_case)
) -> TransferResult:
    return await use_case(character, token)

@router.get('/transfer/rules', response_model=TransferValueCharactersSettingsReadSchema)
async def get_transfer_value_characters_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetTransferValueCharactersSettingsUseCaseProtocol = Depends(get_transfer_rules_use_case)
) -> TransferValueCharactersSettingsReadSchema:
    return await use_case()


@router.put('/{character_id}/ducats', response_model=StatusOkSchema)
async def update_ducats(
    stats: DucatsStat,
    character_id: uuid.UUID = Path(...),
    token: dict = Depends(get_service_token_payload),
    use_case: UpdateCharacterDucatsUseCaseProtocol = Depends(get_character_update_ducats_use_case)
) -> StatusOkSchema:
    return await use_case(character_id, stats)

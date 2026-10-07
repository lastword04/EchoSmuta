from fastapi import APIRouter, Depends, Path, WebSocket, Query, WebSocketDisconnect
from pydantic import ValidationError
import asyncio
import uuid
import json
from typing import Optional
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.chat import ChatSettingsDefaultCreateSchema, ChatSettingsReadSchema
from ...core.depends import get_user_token_payload, get_service_token_payload
from .schemas import (
    IgnoreReadSchema,
    IgnoreRequestSchema,
    MessageRequestSchema,
    MessagePaginationReadSchema,
    ChatSettingsUpdateSchema,
    FavoriteBellsReadSchema,
    FavoriteBellsRequestSchema,
    CharacterOnlinePaginationSchema
)
from .manager.websocket import WebSocketManagerProtocol
from .use_cases.ignore.create import CreateIgnoreUseCaseProtocol
from .use_cases.ignore.delete import DeleteIgnoreUseCaseProtocol
from .use_cases.chat_settings.create_default import CreateDefaultSettingsUseCaseProtocol
from .use_cases.chat_settings.get_for_me import GetMeChatSettingsUseCaseProtocol
from .use_cases.chat_settings.update import UpdateChatSettingsUseCaseProtocol
from .use_cases.chat.send_message import SendMessageUseCaseProtocol
from .use_cases.chat.validate import ValidateConnectProtocol
from .use_cases.chat.rate_limit import RateLimitUseCaseProtocol
from .use_cases.chat.get_history import GetChatHistoryUseCaseProtocol
from .use_cases.bells.create import CreateFavoriteBellsUseCaseProtocol
from .use_cases.bells.delete import DeleteFavoriteBellsUseCaseProtocol
from .use_cases.bells.get_all_for_character import GetAllFavoriteBellsForCharacterUseCaseProtocol
from .use_cases.characters.get_online_characters import GetOnlineCharactersUseCaseProtocol
from .depends import (
    get_create_ignore_use_case,
    get_delete_ignore_use_case,
    get_create_default_chat_use_case,
    get_ws_manager,
    get_validate_connect_use_case,
    get_send_message_use_case,
    get_rate_limit_use_case,
    get_chat_history_use_case,
    get_get_my_settings_use_case,
    get_update_settings_use_case,
    get_create_favorite_bells_use_case,
    get_delete_favorite_bells_use_case,
    get_get_all_for_character_use_case,
    get_get_online_characters_use_case
)
from .exceptions import ChatAuthError, ChatInvalidJSONError, ChatRateLimitExceededError, ChatValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/messages', tags=['Messages'])

@router.get('/characters-online', response_model=CharacterOnlinePaginationSchema)
async def get_characters_online(
    limit: int = Query(10, gt=0, le=100, description="Number of slots to return"),
    offset: int = Query(0, ge=0, description="Number of slots to skip"),
    location_slug: Optional[str] = Query(None, description="Location where characters"),
    room_id: Optional[str] = Query(None, description="Virtual room (house:uuid, inn:inside)"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetOnlineCharactersUseCaseProtocol = Depends(get_get_online_characters_use_case)
) -> CharacterOnlinePaginationSchema:
    return await use_case(
        limit, offset, token, location_slug, room_id
    )
@router.post('/ignore', response_model=IgnoreReadSchema, status_code=201)
async def create_ignore(
    ignore: IgnoreRequestSchema,
    use_case: CreateIgnoreUseCaseProtocol = Depends(get_create_ignore_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> IgnoreReadSchema:
    result = await use_case(
        token=token,
        data=ignore
    )
    return result

@router.delete('/ignore/{ignore_character_id}', response_model=None, status_code=204)
async def delete_ignore(
    ignore_character_id: uuid.UUID = Path(..., description="The ID of the ignore relationship to delete"),
    use_case: DeleteIgnoreUseCaseProtocol = Depends(get_delete_ignore_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> bool:
    result = await use_case(token=token, ignore_character_id=ignore_character_id)
    return result

@router.get('/settings/', response_model=ChatSettingsReadSchema)
async def get_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMeChatSettingsUseCaseProtocol = Depends(get_get_my_settings_use_case)
) -> ChatSettingsReadSchema:
    return await use_case(token)

@router.put('/settings/{settings_id}', response_model=ChatSettingsReadSchema)
async def update_settings(
    settings: ChatSettingsUpdateSchema,
    settings_id: uuid.UUID = Path(..., description="Id settings"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateChatSettingsUseCaseProtocol = Depends(get_update_settings_use_case),
    ws_manager: WebSocketManagerProtocol = Depends(get_ws_manager)
) -> ChatSettingsReadSchema:
    result = await use_case(settings_id, settings, token)
    await ws_manager.publish_settings_updated(token.character_id)
    return result

@router.post('/settings/default', response_model=ChatSettingsReadSchema, status_code=201)
async def create_default_settings(
    settings: ChatSettingsDefaultCreateSchema,
    token: dict = Depends(get_service_token_payload),
    use_case: CreateDefaultSettingsUseCaseProtocol = Depends(get_create_default_chat_use_case)
) -> ChatSettingsReadSchema:
    result = await use_case(data=settings)
    return result

@router.get('/{room}/history', response_model=MessagePaginationReadSchema)
async def get_history(
    room: str = Path(..., description="Chat room"),
    location_slug: Optional[str] = Query(None, description="location for connect in global chat"),
    limit: int = Query(10, ge=1, le=100, description="Limit of message history"),
    offset: int = Query(0,  ge=0, description="Offset of message history"),
    use_case: GetChatHistoryUseCaseProtocol = Depends(get_chat_history_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> MessagePaginationReadSchema:
    return await use_case(room, location_slug, token, limit, offset)

@router.post('/bells', response_model=FavoriteBellsReadSchema, status_code=201)
async def create_bells(
    bells: FavoriteBellsRequestSchema,
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateFavoriteBellsUseCaseProtocol = Depends(get_create_favorite_bells_use_case)
) -> FavoriteBellsReadSchema:
    return await use_case(bells, token)

@router.delete('/bells/{code_bell}', response_model=None, status_code=204)
async def delete_bells(
    code_bell: int = Path(..., description="Code of bell"),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DeleteFavoriteBellsUseCaseProtocol = Depends(get_delete_favorite_bells_use_case)
) -> None:
    await use_case(code_bell, token)
    return None

@router.get('/bell', response_model=list[FavoriteBellsReadSchema])
async def get_bells(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetAllFavoriteBellsForCharacterUseCaseProtocol = Depends(get_get_all_for_character_use_case)
) -> list[FavoriteBellsReadSchema]:
    return await use_case(token)

@router.websocket("/ws/chat/{room}")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str = Path(...),
    token: str = Query(..., description="User token"),
    location_slug: Optional[str] = Query(None, description="location for connect in global chat"),
    validate_connect: ValidateConnectProtocol = Depends(get_validate_connect_use_case), 
    ws_manager: WebSocketManagerProtocol = Depends(get_ws_manager),
    rate_limiter: RateLimitUseCaseProtocol = Depends(get_rate_limit_use_case),
    send_message: SendMessageUseCaseProtocol = Depends(get_send_message_use_case)
):
    
    try:
        user_data = await validate_connect(token, room)
    except Exception:
        error = ChatAuthError()
        await websocket.send_text(json.dumps(error.to_dict(), ensure_ascii=False))
        await websocket.close(code=1008)
        return
    
    # 🔥 ИЗМЕНЕНИЕ 1: Передаём room и получаем уникальный conn_id
    conn_id = await ws_manager.connect(websocket, user_data.character_id, room)

    # 🔥 ИЗМЕНЕНИЕ 2: Передаём conn_id в listen_to_room
    redis_task = asyncio.create_task(
        ws_manager.listen_to_room(websocket, user_data.character_id, room, location_slug, conn_id=conn_id)
    )

    try:
        while True:
            data = await websocket.receive_text()

            if not (await rate_limiter(user_data.character_id)):
                error = ChatRateLimitExceededError(character_id=user_data.character_id)
                await websocket.send_text(json.dumps(error.to_dict(), ensure_ascii=False))
                continue

            try:
                json_data = json.loads(data)
                message_request = MessageRequestSchema.model_validate(json_data)
                # Для мультиплексирования: если указан room в payload — используем его
                target_room = message_request.room if message_request.room else room
                real_room = "private" if message_request.is_private else target_room
                
                await send_message(
                    room=real_room,
                    message=message_request,
                    user_data=user_data
                )
            except json.JSONDecodeError:
                error = ChatInvalidJSONError()
                await websocket.send_text(json.dumps(error.to_dict(), ensure_ascii=False))
            except ValidationError as e:
                error = ChatValidationError(errors=e.errors())
                await websocket.send_text(json.dumps(error.to_dict(), ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
    finally:
        # 🔥 ИЗМЕНЕНИЕ 3: Гарантированно очищаем ИМЕННО ЭТО соединение при любом разрыве
        ws_manager.disconnect(user_data.character_id, conn_id)
        redis_task.cancel()


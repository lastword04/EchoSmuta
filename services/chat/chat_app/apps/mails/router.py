from fastapi import APIRouter, Depends, Response, Path, Query
from typing import Optional
import uuid
from shared.schemas.auth import UserTokenDataReadSchema
from ...core.depends import get_user_token_payload
from .schemas import (
    MailMessageReadSchema,
    MailMessagePaginationResultSchema,
    MailMessageRequestCreateSchema,
    ReadStatusSchema,
    MailRecieveSettingsReadSchema
)
from .use_cases.create import CreateMailMessageUseCaseProtocol
from .use_cases.get_my import GetMyMailMessageUseCaseProtocol
from .use_cases.get_for_me import GetMailMessageForMeUseCaseProtocol
from .use_cases.delete_for_recipient import DeleteForRecipientMailMessageUseCaseProtocol
from .use_cases.delete_for_sender import DeleteForSenderMailMessageUseCaseProtocol
from .use_cases.update_all_messages_to_is_read import UpdateMailMessagesToIsReadUseCaseProtocol
from .use_cases.check_not_is_read_messages import CheckNotIsReadMessageUseCaseProtocol
from .use_cases.mails_settings.create import CreateMailsSettingsUseCaseProtocol
from .use_cases.mails_settings.get import GetMailsSettingsUseCaseProtocol
from .use_cases.mails_settings.delete import DeleteMailsSettingsUseCaseProtocol
from .depends import (
    get_create_mail_message_use_case,
    get_get_my_mail_message_use_case,
    get_get_mail_message_for_me_use_case,
    get_delete_for_recipient_mail_message_use_case,
    get_delete_for_sender_mail_message_use_case,
    get_update_all_messages_to_is_read_use_case,
    get_check_not_is_read_message_use_case,
    get_get_mails_settings_use_case,
    get_create_mails_settings_use_case,
    get_delete_mails_settings_use_case
)


router = APIRouter(prefix='/api/mails', tags=['Mails'])

@router.post('/settings', response_model=MailRecieveSettingsReadSchema, status_code=201)
async def create_mail_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CreateMailsSettingsUseCaseProtocol = Depends(get_create_mails_settings_use_case)
) -> MailRecieveSettingsReadSchema:
    return await use_case(token)

@router.get('/settings', response_model=Optional[MailRecieveSettingsReadSchema])
async def get_mail_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: GetMailsSettingsUseCaseProtocol = Depends(get_get_mails_settings_use_case)
) -> Optional[MailRecieveSettingsReadSchema]:
    return await use_case(token)

@router.delete('/settings', response_model=None, status_code=204)
async def delete_mail_settings(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: DeleteMailsSettingsUseCaseProtocol = Depends(get_delete_mails_settings_use_case)
) -> None:
    await use_case(token)

    return None
    

@router.post('/', response_model=MailMessageReadSchema, status_code=201)
async def create_mail_message(
    mail_message: MailMessageRequestCreateSchema,
    use_case: CreateMailMessageUseCaseProtocol = Depends(get_create_mail_message_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> MailMessageReadSchema:
    result = await use_case(
        token=token,
        message=mail_message
    )
    return result

@router.get('/my', response_model=MailMessagePaginationResultSchema)
async def get_my_mail_messages(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_case: GetMyMailMessageUseCaseProtocol = Depends(get_get_my_mail_message_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> MailMessagePaginationResultSchema:
    result = await use_case(
        limit=limit,
        offset=offset,
        token=token
    )
    return result

@router.get('/', response_model=MailMessagePaginationResultSchema)
async def get_mail_messages(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_case: GetMailMessageForMeUseCaseProtocol = Depends(get_get_mail_message_for_me_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> MailMessagePaginationResultSchema:
    result = await use_case(
        limit=limit,
        offset=offset,
        token=token
    )
    return result

# @router.delete('/{message_id}', status_code=204)
# async def delete_mail_message(
#     message_id: uuid.UUID = Path(...),
#     use_case: DeleteMailMessageUseCaseProtocol = Depends(get_delete_mail_message_use_case),
#     token: UserTokenDataReadSchema = Depends(get_user_token_payload)
# ) -> Response:
#     await use_case(
#         message_id=message_id,
#         token=token
#     )
#     return Response(status_code=204)

@router.delete('/{message_id}/recipient', response_model=None, status_code=204)
async def delete_for_recipient(
    message_id: uuid.UUID = Path(...),
    use_case: DeleteForRecipientMailMessageUseCaseProtocol = Depends(get_delete_for_recipient_mail_message_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> Response:
    await use_case(
        message_id=message_id,
        token=token
    )
    return None

@router.delete('/{message_id}/sender', response_model=None, status_code=204)
async def delete_for_sender(
    message_id: uuid.UUID = Path(...),
    use_case: DeleteForSenderMailMessageUseCaseProtocol = Depends(get_delete_for_sender_mail_message_use_case),
    token: UserTokenDataReadSchema = Depends(get_user_token_payload)
) -> Response:
    await use_case(
        message_id=message_id,
        token=token
    )
    return None

@router.put('/read', response_model=bool)
async def read_mails_messages(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: UpdateMailMessagesToIsReadUseCaseProtocol = Depends(get_update_all_messages_to_is_read_use_case),
) -> UpdateMailMessagesToIsReadUseCaseProtocol:
    return await use_case(token)

@router.get('/read', response_model=ReadStatusSchema)
async def all_is_read_mails(
    token: UserTokenDataReadSchema = Depends(get_user_token_payload),
    use_case: CheckNotIsReadMessageUseCaseProtocol = Depends(get_check_not_is_read_message_use_case)
) -> ReadStatusSchema:
    
    is_read = await use_case(token)
    return ReadStatusSchema(
        all_is_read=is_read
    )

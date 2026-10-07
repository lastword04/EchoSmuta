from fastapi import APIRouter, Depends
from ...core.depends import get_service_token_payload
from shared.schemas.email import EmailResetPasswordSchema, EmailLogReadSchema
from .use_cases.send_and_save_email import SendAndSaveEmailUseCaseProtocol
from .depends import get_send_and_save_email_use_case


router = APIRouter(prefix='/api/emails', tags=['Emails'])


@router.post("/reset-password", response_model=EmailLogReadSchema)
async def reset_password(
    email: EmailResetPasswordSchema,
    token: str = Depends(get_service_token_payload),
    send: SendAndSaveEmailUseCaseProtocol = Depends(get_send_and_save_email_use_case)
):
    return await send(email)
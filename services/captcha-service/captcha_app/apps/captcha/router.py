from fastapi import APIRouter, Depends
from shared.schemas.captcha import CaptchaVerificationRequest, GeneratedCaptchaResponse
from shared.schemas.base import StatusOkSchema
from ...core.depends import get_service_token_payload
from .use_cases.create_captcha import CreateCaptchaUseCaseProtocol
from .use_cases.verify_captcha import VerifyCaptchaUseCaseProtocol
from .depends import (
    get_captcha_create_use_case,
    get_captcha_verify_use_case
)
router = APIRouter(prefix='/api/captcha', tags=['Captcha'])


@router.post('/', response_model=GeneratedCaptchaResponse, status_code=201)
async def create_captcha(use_case: CreateCaptchaUseCaseProtocol = Depends(get_captcha_create_use_case)) -> GeneratedCaptchaResponse:
    result = await use_case()
    return result


@router.post('/verify', response_model=StatusOkSchema, status_code=200)
async def verify_captcha(data: CaptchaVerificationRequest, 
                          token: dict = Depends(get_service_token_payload),
                          use_case: VerifyCaptchaUseCaseProtocol = Depends(get_captcha_verify_use_case)
                          ) -> None:
    return await use_case(data)
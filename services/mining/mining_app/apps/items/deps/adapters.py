"""Провайдеры адаптеров и сквозных инфраструктурных сервисов.

Не привязаны к домену: HTTP-клиенты внешних сервисов, events-паблишеры
и сервис шаблонов. Импортируются всеми доменными deps-модулями.
"""
from fastapi import Depends

from ....settings import Settings, get_settings
from ...resources.depends import get_text_template_service
from ..adapters.captcha import CaptchaServiceClient, CaptchaServiceClientProtocol
from ..adapters.characters import CharacterServiceClient, CharacterServiceClientProtocol
from ..adapters.file_storage import FileServiceClient, FileServiceClientProtocol
from ..services.adapters.item_templates import (
    ItemTemplateService,
    ItemTemplateServiceProtocol,
)


# adapters
def get_character_service_client(
    settings: Settings = Depends(get_settings)
) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(
        base_url=settings.character_service_app.base_url,
        stats_base_url=settings.character_service_app.stats_base_url,
    )

def get_file_service_client(
    settings: Settings = Depends(get_settings)
) -> FileServiceClientProtocol:
    return FileServiceClient(
        base_url=settings.file_service_app.base_url
    )

def get_captcha_service_client(
    settings: Settings = Depends(get_settings)
) -> CaptchaServiceClientProtocol:
    return CaptchaServiceClient(
        base_url=settings.captcha_service_app.base_url
    )


def get_item_template_service(
    template_service = Depends(get_text_template_service),
) -> ItemTemplateServiceProtocol:
    return ItemTemplateService(template_service)

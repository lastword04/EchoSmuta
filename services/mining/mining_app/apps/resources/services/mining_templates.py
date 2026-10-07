from typing import Protocol

from shared.enums import ResultStatus
from shared.services.templates import TextTemplateServiceProtocol

from ..enums import MiningStatus


class MiningTemplateServiceProtocol(Protocol):
    def get_message(self, character_location_slug: str, 
                    mining_status: MiningStatus, 
                    result_status: ResultStatus | None = None,
                    **kwargs
                    ) -> str:
        ...


class MiningTemplateService(MiningTemplateServiceProtocol):
    def __init__(self, template_service: TextTemplateServiceProtocol):
        self.template_service = template_service

    def get_message(self, character_location_slug: str, 
                    mining_status: MiningStatus, 
                    result_status: ResultStatus | None = None,
                    **kwargs
                    ) -> str:
        str_status = ""
        if mining_status == MiningStatus.IN_PROGRESS:
            str_status = "progress"
        else:
            str_status = result_status.value

        if not str_status:
            raise ValueError("Impossible values mining for calculate template")
        
        location_name = character_location_slug.split('.')[-1]
        key = f"mining_locations_{location_name}_resources_{str_status}"
        return self.template_service.get_template(key, **kwargs)
        

        
        

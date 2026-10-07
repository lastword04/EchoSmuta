import uuid
from shared.services.templates import TextTemplateServiceProtocol
from .....core.use_cases import UseCaseProtocol
from ...schemas import MessageReadSchema
from .send_system_message import SendSystemMessageUseCaseProtocol
from ...enums import MessageType

class SendDefaultMessagesUseCaseProtocol(UseCaseProtocol[tuple[MessageReadSchema, MessageReadSchema]]):
    async def __call__(self, character_id: uuid.UUID, character_name: str, is_main: bool) -> tuple[MessageReadSchema, MessageReadSchema]:
        ...

class SendDefaultMessagesUseCase(SendDefaultMessagesUseCaseProtocol):
    def __init__(self, send_system_msg: SendSystemMessageUseCaseProtocol, 
                 template_service: TextTemplateServiceProtocol,
                 frontend_url: str):
        self.send_system_msg = send_system_msg
        self.template_service = template_service
        self.frontend_url = frontend_url

    async def __call__(self, character_id: uuid.UUID, character_name: str, is_main: bool) -> tuple[MessageReadSchema, MessageReadSchema]:
        if is_main:
            character_name_html = f"<strong>{character_name}</strong>"
        else:
            character_name_html = character_name

        all_template_key = "character_play_info_all"
        content = self.template_service.get_template(all_template_key, 
                                                     frontend_url=self.frontend_url,
                                                     character_id=character_id,
                                                     character_name_html=character_name_html
                                                     )
        
        create_character_info_msg = await self.send_system_msg(
            room="system",
            content=content,
            message_type=MessageType.SYSTEM_CREATE_CHARACTER,
            is_trade=False
        )
        hello_character_msg = None
        
        if is_main:
            self_template_key = "character_play_info_self"

            hello_character_content = self.template_service.get_template(self_template_key)
            
            hello_character_msg = await self.send_system_msg(
                room="system",
                content=hello_character_content,
                message_type=MessageType.SYSTEM_PRIVATE,
                is_trade=False,
                target_user_ids=[character_id]
            )

        return create_character_info_msg, hello_character_msg
from fastapi import status 
import uuid
from typing import Optional
from shared.exceptions import CoreException

class CannotSendMessageToSelfError(CoreException):
    """
    Ошибка, возникающая при попытке отправить сообщение самому себе.
    """
    def __init__(
        self,
        sender_id: Optional[uuid.UUID] = None,
        recipient_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "CANNOT_SEND_MESSAGE_TO_SELF",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot send message to self. A character cannot send a message to themselves."
        
        if extras is None:
            extras = {}
        
        if sender_id is not None:
            extras["sender_id"] = str(sender_id)
        if recipient_id is not None:
            extras["recipient_id"] = str(recipient_id)
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CannotSendMessageToSelfError",
            extras=extras,
            headers=headers
        )


class CannotSendMessageToCharacterError(CoreException):
    """
    Ошибка, возникающая при попытке отправить сообщение персонажу, которому нельзя отправить письмо.
    """
    def __init__(
        self,
        sender_id: Optional[uuid.UUID] = None,
        recipient_id: Optional[uuid.UUID] = None,
        detail: str = None,
        error_code: str = "CANNOT_SEND_MESSAGE_TO_CHARACTER",
        extras: dict = None,
        headers: dict = None
    ) -> None:
        if detail is None:
            detail = "Cannot send message to character. This character has limited who can send him messages."
        
        if extras is None:
            extras = {}
        
        if sender_id is not None:
            extras["sender_id"] = str(sender_id)
        if recipient_id is not None:
            extras["recipient_id"] = str(recipient_id)
            
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            error_type="CannotSendMessageToCharacterError",
            extras=extras,
            headers=headers
        )
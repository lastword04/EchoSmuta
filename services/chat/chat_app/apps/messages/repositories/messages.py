from ....core.repositories.base_repository import BaseRepositoryImpl
from ..models import Message
from ..schemas import MessageCreateSchema, MessageUpdateSchema, MessageReadSchema

class MessageRepositoryProtocol(BaseRepositoryImpl[Message, MessageReadSchema, MessageCreateSchema, MessageUpdateSchema]):
    pass

class MessageRepository(MessageRepositoryProtocol):
    pass
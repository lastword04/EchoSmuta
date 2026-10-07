from enum import Enum

class SenderStatus(str, Enum):
    USER = "user"
    SYSTEM = "system"
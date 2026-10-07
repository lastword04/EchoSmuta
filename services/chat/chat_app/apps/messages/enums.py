from enum import Enum

class MessageType(str, Enum):
    SYSTEM_GLOBAL = "system_global"
    SYSTEM_CREATE_CHARACTER = "system_create_character"
    SYSTEM_PLAY_CHARACTER = "system_play_character"
    SYSTEM_PRIVATE = "system_private"
    IGNORE = "ignore"
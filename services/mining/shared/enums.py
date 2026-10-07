from enum import Enum

class UserRole(str, Enum):
    """
    Enum for user roles.
    """
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class Race(str, Enum):
    """
    Enum for character races.
    """
    HUMAN = "human"
    ELF = "elf"
    ORC = "orc"

class LocationType(str, Enum):
    RESOURCES = "resources"
    ITEMS = "items"
    REST = "rest"
    OTHER = "other"

class ResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class MonsterAttackStatus(str, Enum):
    PROCESS = "process"
    SUCCESS = "success"
from enum import Enum


class MiningStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
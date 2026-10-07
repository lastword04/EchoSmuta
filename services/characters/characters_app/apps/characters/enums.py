from enum import Enum

class ActionType(str, Enum):
    PLAY = "play"
    QUIT = "quit"
    LOGOUT = "logout"
    BUTTON_CLICK = "button_click"
    ITEM_USE = "item_use"
    QUEST_START = "quest_start"
    QUEST_COMPLETE = "quest_complete"



class CharacterSkillType(str, Enum):
    STANDARD = "standard"
    MASTERSHIP = "mastership"
    
    @property
    def coefficient(self) -> float:
        coefficients = {
            CharacterSkillType.STANDARD: 1.68,
            CharacterSkillType.MASTERSHIP: 19.32,
        }
        return coefficients[self]
    
    
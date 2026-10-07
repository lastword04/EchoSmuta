from enum import Enum

class EventType(str, Enum):
    LOGIN = "login"
    PLAY = "play"
    QUIT = "quit"
    REGISTER = "register"
    LOGOUT = "logout"
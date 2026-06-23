from enum import Enum, auto


class Behavior(Enum):
    BOOTING = auto()
    SEARCH_BALL = auto()
    FOLLOW_BALL = auto()
    DONE = auto()
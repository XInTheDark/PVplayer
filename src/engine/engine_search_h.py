import chess
import chess.engine

import engine_utils as utils
from engine_ucioption import option

from collections import deque

# Constants
VALUE_INFINITE = 999999
VALUE_NONE = 9999999
VALUE_MATE = 100000
VALUE_DRAW = 0
MAX_DEPTH = 256
MAX_HORIZON = 30


class Value:
    """Stores a value in centipawns.
     If `pov` is provided, then it will always be from the perspective of `pov`,
     i.e. larger is always better for `pov`.
     """
    value = None
    pov = None
    
    def __init__(self, value=VALUE_NONE, pov=None):
        if type(value) == int:
            self.value = value
        elif type(value) == chess.engine.PovScore and pov is None:
            self.value = value.relative.score(mate_score=VALUE_MATE)
        elif type(value) == chess.engine.PovScore and pov is not None:
            self.value = value.white().score(mate_score=VALUE_MATE)
            if pov == chess.BLACK:
                self.value = -self.value
            self.pov = pov
        elif type(value) == chess.engine.Score:
            self.value = value.score(mate_score=VALUE_MATE)
        elif type(value) == chess.engine.Cp:
            self.value = value.score(mate_score=VALUE_MATE)
        self.pov = pov
    
    def __int__(self):
        return self.value
    
    def to_cp(self):
        return self.value  # from side to move's POV
    
    def __str__(self):
        return utils.cp_to_score(self.value)
    
    def __uci_str__(self):
        return str(self.value)
    
    def __lt__(self, other):
        if type(other) == int:
            return self.value < other
        if other.pov is not None and other.pov != self.pov:
            return self.value < -other.value
        return self.value < other.value
    
    def __gt__(self, other):
        if type(other) == int:
            return self.value > other
        if other.pov is not None and other.pov != self.pov:
            return self.value > -other.value
        return self.value > other.value
    
    def __eq__(self, other):
        if type(other) == int:
            return self.value == other
        if other.pov is not None and other.pov != self.pov:
            return self.value == -other.value
        return self.value == other.value
    
    def __le__(self, other):
        if type(other) == int:
            return self.value <= other
        if other.pov is not None and other.pov != self.pov:
            return self.value <= -other.value
        return self.value <= other.value
    
    def __ge__(self, other):
        if type(other) == int:
            return self.value >= other
        if other.pov is not None and other.pov != self.pov:
            return self.value >= -other.value
        return self.value >= other.value
    
    # +, -, *, /, //
    def __add__(self, other):
        if type(other) == int:
            return self.value + other
        return self.value + other.value
    
    def __sub__(self, other):
        if type(other) == int:
            return self.value - other
        return self.value - other.value
    
    def __mul__(self, other):
        if type(other) == int:
            return self.value * other
        return self.value * other.value
    
    def __truediv__(self, other):
        if type(other) == int:
            return self.value / other
        return self.value / other.value
    
    def __floordiv__(self, other):
        if type(other) == int:
            return self.value // other
        return self.value // other.value
    
    def white(self):
        if self.pov:
            return self.value if self.pov == chess.WHITE else -self.value
    
    def to_pov(self, pov):
        if self.pov is not None:
            return Value(self.value, pov) if self.pov == pov else Value(-self.value, pov)
        return Value(self.value, pov)


class RunningAverage:
    max_count = 1024
    total = 0
    count = 0
    values = deque()
    
    def __init__(self, max_count: int = 1024):
        assert max_count > 0
        self.max_count = max_count
    
    def add(self, value):
        self.total += value
        self.count += 1
        if self.count > self.max_count:
            self.total -= self.values.popleft()  # removes the oldest value
            self.count -= 1
        self.values.append(value)
    
    def value(self):
        return self.total / self.count if self.count > 0 else 0
    
    def clear(self):
        self.total = 0
        self.count = 0
        self.earliest = 0

    def __str__(self):
        return str(self.value())
    
    def __int__(self):
        return int(self.value())
    
    
def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

def GET_MAX_DEPTH():
    return MAX_DEPTH

def GET_MAX_HORIZON():
    return MAX_HORIZON

def GET_MAX_MOVES():
    return option("MAX_MOVES")
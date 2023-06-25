import chess, chess.engine

import utils


class Value:
    """Stores a value in centipawns.
     If `pov` is provided, then it will always be from the perspective of `pov`,
     i.e. larger is always better for `pov`.
     """
    value = None
    pov = None
    
    def __init__(self, value, pov=None):
        if type(value) == int:
            self.value = value
        elif type(value) == chess.engine.PovScore and pov is None:
            self.value = value.relative.score(mate_score=100000)
        elif type(value) == chess.engine.PovScore and pov is not None:
            self.value = value.white().score(mate_score=100000)
            if pov == chess.BLACK:
                self.value = -self.value
            self.pov = pov
        elif type(value) == chess.engine.Score:
            self.value = value.score(mate_score=100000)
        elif type(value) == chess.engine.Cp:
            self.value = value.score(mate_score=100000)
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
        
        
def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)
import math

import chess

import engine_utils as utils
from engine_ucioption import *


class Time:
    """
    Store basic information for current game,
    and provides functions for calculation of time.
    Time units are in milliseconds.
    """
    wtime: int = 0
    winc: int = 0
    btime: int = 0
    binc: int = 0
    
    time: [int, int] = [0, 0]  # black (0), white (1)
    inc: [int, int] = [0, 0]
    
    optTime = maxTime = 0
    
    def __init__(self, wtime: int = 0, btime: int = 0, winc: int = 0, binc: int = 0):
        self.wtime = wtime
        self.winc = winc
        self.btime = btime
        self.binc = binc
        self.time = [btime, wtime]
        self.inc = [binc, winc]
    
    def get_time(self, c: chess.Color):
        return self.time[int(c)]
    
    def get_inc(self, c: chess.Color):
        return self.inc[int(c)]
    
    def init(self, us: chess.Color, ply: int):
        """Much of the calculation algorithm is derived from Stockfish."""
        if self.time[us] == 0:
            return
        
        overhead = option("Move Overhead")
        
        timeLeft = max(1, self.time[us] + self.inc[us] * 49 - overhead)
        
        # Use extra time with larger increments
        # Also use less time with zero increment
        optExtra = utils.clamp(1.0 + 0.4 * math.log10(600 * self.inc[us] / self.time[us]), 1.0, 1.25) \
            if self.inc[us] > 0 else 0.8
        
        optScale = min((0.88 + ply / 116.4) / 50,
                       0.88 * self.time[us] / timeLeft) * optExtra
        maxScale = min(3.0 + 0.05 * ply, 6.5)
        
        # Never use more than x% of the available time for this move (scale based on ply)
        self.optTime = max(1, int(optScale * timeLeft))
        maxTimePercent = min(0.70 + 0.001 * ply, 0.90)
        self.maxTime = int(min(maxTimePercent * self.time[us] - overhead, maxScale * self.optTime))
        self.optTime = min(self.optTime, self.maxTime)  # optTime <= maxTime
    
    def to_Limit(self):
        return self.wtime / 1000, self.btime / 1000, self.winc / 1000, self.binc / 1000
import chess
import utils

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
    
    def __init__(self, wtime: int=0, winc: int=0, btime: int=0, binc: int=0):
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
        optExtra = utils.clamp(1.0 + 12.0 * self.inc[us] / self.time[us], 1.0, 1.2)
        
        # Use more time at start of game
        startExtra = 1 + (16 - ply) * 0.15 if ply < 16 else 1.0

        optScale = min((0.88 + ply / 116.4) / 50,
            0.88 * self.time[us] / timeLeft) * optExtra * startExtra
        maxScale = 6.3
        
        # Never use more than 80% of the available time for this move
        self.optTime = max(1, int(optScale * timeLeft))
        self.maxTime = int(min(0.8 * self.time[us] - overhead, maxScale * self.optTime))
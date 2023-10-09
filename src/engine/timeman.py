import math

import chess

import utils as utils
from ucioption import *


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

    us: chess.Color = None
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
        self.us = us
        them = not us

        if self.time[us] == 0:
            return

        overhead = option("Move Overhead")

        timeLeft = max(1, self.time[us] + self.inc[us] * 49 - overhead)

        # Use extra time with larger increments
        # Also use less time with zero increment
        optExtra = utils.clamp(1.0 + 0.4 * math.log10(600 * self.inc[us] / self.time[us]), 1.0, 1.25) \
            if self.inc[us] > 0 else 0.8

        # Use more time if we have much more time than the opponent
        advExtra = 1.0
        if 0 < self.time[them] < self.time[us]:
            timeRatio = self.time[us] / self.time[them]
            incRatio = self.inc[them] / self.inc[us]
            advExtra = 1.0 + 0.2 * math.log10(timeRatio) + 0.1 * timeRatio - 1.0 * math.log10(incRatio)
            advExtra = utils.clamp(advExtra, 1.0, 3.0)

        optScale = min((0.88 + ply / 116.4) / 50,
                       0.88 * self.time[us] / timeLeft) * optExtra * advExtra
        maxScale = min(3.0 + 0.05 * ply, 6.5)

        # Never use more than x% of the available time for this move (scale based on ply)
        self.optTime = max(1, int(optScale * timeLeft))
        maxTimePercent = min(0.70 + 0.001 * ply, 0.90)
        self.maxTime = int(min(maxTimePercent * self.time[us] - overhead, maxScale * self.optTime))
        self.optTime = min(self.optTime, self.maxTime)  # optTime <= maxTime

    def to_Limit(self):
        return self.wtime / 1000, self.btime / 1000, self.winc / 1000, self.binc / 1000

    def useTimeMan(self):
        if self.us is None:
            return self.wtime > 0 or self.btime > 0
        else:
            return self.get_time(self.us) > 0 or self.optTime > 0 or self.maxTime > 0

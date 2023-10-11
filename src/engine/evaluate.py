import chess
import chess.engine

from ucioption import *
from timeman import Time

import os

engine: chess.engine.SimpleEngine = None
engine_options = {
    "Threads": option("Threads"),
    "Hash": option("Hash"),
}


def init_engine():
    global engine
    if engine is not None:
        engine.quit()

    ENGINE_PATH = option("ENGINE_PATH")
    ENGINE_MISSING = False
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    except FileNotFoundError:
        ENGINE_MISSING = True

    try:
        info = engine.analyse(chess.Board(), chess.engine.Limit(nodes=10))
    except Exception:
        ENGINE_MISSING = True

    if ENGINE_MISSING:
        print("Engine (specified in ENGINE_PATH option) not found! Attempting to download Stockfish.")
        # Download engine
        from download import download_stockfish
        try:
            ENGINE_PATH = download_stockfish()
        except Exception as e:
            print("Failed to download engine. Error:", e)
            os._exit(0)

        options["ENGINE_PATH"] = ENGINE_PATH
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
        print("Engine downloaded successfully.")

    setoptions_engine()


def setoptions_engine():
    global engine, engine_options
    # UCI options

    # Update default engine options
    engine_options["Threads"] = option("Threads")
    engine_options["Hash"] = option("Hash")

    for name, value in engine_options.items():
        try:
            engine.configure({name: value})
        except:
            pass  # sometimes there may be unsupported options


def __engine__(pos: chess.Board, depth: int = None, nodes: int = None,
               movetime: float = None, timeMan: Time = None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    global engine

    # Create a new limit
    if timeMan and movetime:
        timeMan = None  # movetime takes precedence

    useTimeMan = timeMan is not None and timeMan.useTimeMan()
    useMoveTime = useTimeMan and timeMan.optTime == timeMan.maxTime

    limit = chess.engine.Limit(depth=depth, nodes=nodes)

    if useTimeMan and not useMoveTime:
        wtime, btime, winc, binc = timeMan.to_Limit()
        limit = chess.engine.Limit(white_clock=wtime, black_clock=btime, white_inc=winc, black_inc=binc)
    elif movetime:
        limit = chess.engine.Limit(time=movetime)
    elif useMoveTime:
        limit = chess.engine.Limit(time=timeMan.maxTime / 1000)

    # Evaluate with engine
    result = engine.analyse(pos, limit)
    return result

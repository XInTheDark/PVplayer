import chess
import chess.engine

from engine_ucioption import *
from engine_timeman import Time

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
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    except FileNotFoundError:
        return
    
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
        
    if timeMan:
        wtime, btime, winc, binc = timeMan.to_Limit()
        limit = chess.engine.Limit(white_clock=wtime, black_clock=btime, white_inc=winc, black_inc=binc)
    else:
        limit = chess.engine.Limit(depth=depth, nodes=nodes, time=movetime)
    
    # Evaluate with engine
    result = engine.analyse(pos, limit)
    return result

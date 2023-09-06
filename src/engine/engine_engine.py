import chess
import chess.engine

from engine_ucioption import *

engine: chess.engine.SimpleEngine = None


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
    global engine
    # UCI options
    engine_options = {
        "Threads": option("Threads"),
        "Hash": option("Hash"),
    }
    for name, value in engine_options.items():
        engine.configure({name: value})


def __engine__(pos: chess.Board, depth: int = None, nodes: int = None,
               time: float = None, mate: int = None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    global engine
    
    # Create a new limit
    limit = chess.engine.Limit(depth=depth, nodes=nodes, time=time, mate=mate)
    
    # Evaluate with engine
    result = engine.analyse(pos, limit)
    return result

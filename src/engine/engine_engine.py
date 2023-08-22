import chess, chess.engine

from engine_ucioption import *

engine: chess.engine.SimpleEngine = None

def init_engine():
    global engine
    ENGINE_PATH = option("ENGINE_PATH")
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    # UCI options
    engine_options = {
        "Threads": option("Threads"),
        "Hash": option("Hash"),
    }
    for name, value in engine_options.items():
        engine.configure({name: value})
        
def __engine__(fen: str = None, depth: int = None, nodes: int = None,
               time: int = None, mate: int = None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    global engine
    
    # Create board
    board = chess.Board(fen)
    
    # Create a new limit
    limit = chess.engine.Limit(depth=depth, nodes=nodes, time=time, mate=mate)
    
    # Evaluate with engine
    result = engine.analyse(board, limit)
    return result
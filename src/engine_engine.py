import chess, chess.engine
import yaml
import utils
from engine_ucioption import *

ENGINE_PATH = option("ENGINE_PATH")
engine_options = {
    "Threads": option("Threads"),
    "Hash": option("Hash"),
}

def __engine__(fen: str = None, depth: int = None, nodes: int = None, time: int = None, mate: int = None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    # 1. Create a new engine
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    
    # Set options
    for name, value in engine_options.items():
        engine.configure({name: value})
    
    # 2. Create board
    board = chess.Board(fen)
    
    # 3. Create a new limit
    limit = chess.engine.Limit(depth=depth, nodes=nodes, time=time, mate=mate)
    
    # 4. Evaluate with engine
    # We prefer to pass the entire moves list to the engine, so that it is not
    # blind to threefold repetition.
    if fen:
        result = engine.analyse(board, limit)
    else:  # we use ROOT_BOARD in order to preserve move stack
        result = engine.analyse(utils.ROOT_BOARD, limit)
    
    # 5. Close the engine
    engine.quit()
    
    # 6. Return the info
    return result
import chess, chess.engine

from engine_ucioption import *

def __engine__(fen: str = None, depth: int = None, nodes: int = None, time: int = None, mate: int = None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    
    # UCI options
    ENGINE_PATH = option("ENGINE_PATH")
    engine_options = {
        "Threads": option("Threads"),
        "Hash": option("Hash"),
    }
    
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
    result = engine.analyse(board, limit)
    
    # 5. Close the engine
    engine.quit()
    
    # 6. Return the info
    return result
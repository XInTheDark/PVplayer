import chess, chess.engine
import yaml

with open("config.yml", "r") as f:
    ENGINE_PATH = yaml.safe_load(f)["ENGINE_PATH"]

def __engine__(fen: str, depth: int=None, nodes: int=None, time: int=None, mate: int=None):
    """
    fen: FEN string
    depth: depth to search to
    nodes: number of nodes to search
    time: time to search for
    """
    # 1. Create a new engine
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    
    # 2. Create board
    board = chess.Board(fen)
    
    # 3. Create a new limit
    limit = chess.engine.Limit(depth=depth, nodes=nodes, time=time, mate=mate)
    
    # 4. Evaluate with engine
    result = engine.analyse(board, limit=limit)
    
    # 5. Close the engine
    engine.quit()
    
    # 6. Return the info
    return result
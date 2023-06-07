import chess, chess.engine
import engine
import simple
import printBoard

def tracePV(startfen: str, MAX_MOVES=20, depth:int=None, nodes:int=None, time:int=None, mate:int=None, print_board=True):
    """
    'Trace' the PV of a given FEN and keep calculating the next PV. This repeats until the end of the game
    or until the maximum number of iterations is reached.
    """
    MAX_ITER = 40
    board = chess.Board(startfen)
    
    i = 1
    while i <= MAX_ITER:
        info: chess.engine.InfoDict = engine.__engine__(board.fen(), depth=depth, nodes=nodes, time=time, mate=mate)
        pv = info["pv"]
        # only take the first MAX_MOVES of the pv because it can be increasingly unreliable
        pv = pv[:MAX_MOVES]
        board = simple.push_pv(board, pv)
        
        # other related info
        score = info["score"]  # type chess.engine.PovScore
        score = str(score.white())  # in CP
        
        _depth = info["depth"]
        _seldepth = info["seldepth"]
        _nodes = info["nodes"]
        _nps = info["nps"]
        _time = info["time"]
        
        print(f"Iteration {i} | Eval: {score} | depth: {_depth}/{_seldepth} | nodes: {_nodes} (nps {_nps}) | time: {_time}s")
        print(f"Iteration {i} | Traced FEN: {board.fen()}")
        if print_board:
            printBoard.printBoard(board.fen())
        
        i += 1
        
    
    
def main():
    startfen = input("FEN > ")
    
    # Sample usage
    tracePV(startfen, depth=30, MAX_MOVES=10)
    
    
if __name__ == "__main__":
    main()
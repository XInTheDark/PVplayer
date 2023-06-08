import chess, chess.engine
import yaml

import engine
import simple
import printBoard
import query_tb

def tracePV(startfen: str, MAX_MOVES=20, MAX_ITER=100, depth:int=None, nodes:int=None, time:int=None, mate:int=None,
            print_board=True, stop_on_tbhit=True, query_on_tbhit=True):
    """
    'Trace' the PV of a given FEN and keep calculating the next PV. This repeats until the end of the game
    or until the maximum number of iterations is reached.
    """
    board = chess.Board(startfen)
    
    if not depth:
        depth = None
    if not nodes:
        nodes = None
    if not time:
        time = None
    if not mate:
        mate = None
    
    # if no parameters are given, default to 10 seconds
    if not depth and not nodes and not time and not mate:
        time = 10
        
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
            
        if board.is_game_over(claim_draw=True):
            print("Game over, stopping!")
            return

        # Query tablebase if possible
        if query_on_tbhit and len(board.piece_map()) <= 7:
            print("Tablebase position reached (<= 7 pieces), querying...")
            # Get eval
            tb_eval = query_tb.query_tablebase_eval(board)
            if tb_eval is None:
                print("Tablebase error, stopping!")
                return

            eval_ = tb_eval[0]
            dtm = tb_eval[1]
            if dtm:
                print(f"Tablebase eval: {eval_} (DTM {dtm})")
            else:
                print(f"Tablebase eval: {eval_}")

            # Get best line (until end of game)
            tb_pv = query_tb.query_tablebase_pv(board)
            if tb_pv is None:
                print("Tablebase error, stopping!")
                return

            board = simple.push_pv(board, tb_pv)
            print(f"Traced FEN: {board.fen()}")
            if print_board:
                printBoard.printBoard(board.fen())
                
        if stop_on_tbhit and len(board.piece_map()) <= 7:
            print("Tablebase position reached (<= 7 pieces), stopping!")
            return
        
        i += 1
        
    
    
def main():
    startfen = input("FEN > ")
    
    # Sample usage
    # tracePV(startfen, depth=30, MAX_MOVES=10)
    
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)
        depth = int(config["DEPTH"])
        nodes = int(config["NODES"])
        time = int(config["TIME"])
        mate = int(config["MATE"])
        max_moves = int(config["MAX_MOVES"])
        max_iter = int(config["MAX_ITER"])
        print_board = bool(config["PRINT_BOARD"])
        stop_on_tbhit = bool(config["STOP_ON_TBHIT"])
        query_on_tbhit = bool(config["QUERY_ON_TBHIT"])
        
        
    tracePV(startfen, depth=depth, nodes=nodes, time=time, mate=mate, MAX_MOVES=max_moves, MAX_ITER=max_iter,
            print_board=print_board, stop_on_tbhit=stop_on_tbhit, query_on_tbhit=query_on_tbhit)
    simple.write_pgn()
    
    
    
if __name__ == "__main__":
    main()
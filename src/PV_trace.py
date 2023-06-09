import chess, chess.engine
import yaml

import engine
import utils
import printBoard
import query_tb

def tracePV(startfen: str, MAX_MOVES=20, MAX_ITER=100, depth:int=None, nodes:int=None, time:int=None, mate:int=None,
            print_board=True, stop_on_tbhit=True, query_on_tbhit=True, stop_on_draw=0):
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
    
    # if no parameters are given, default to 2M nodes
    if not depth and not nodes and not time and not mate:
        nodes = 2000000
        
    i = 1
    drawn_moves_count = 0
    
    while i <= MAX_ITER:
        info: chess.engine.InfoDict = engine.__engine__(board.fen(), depth=depth, nodes=nodes, time=time, mate=mate)
        pv = info["pv"]
        # only take the first MAX_MOVES of the pv because it can be increasingly unreliable
        pv = pv[:MAX_MOVES]
        
        # other related info
        score = info["score"] = utils.cp_to_score(info["score"])  # type: str
        
        _depth = info["depth"]
        _seldepth = info["seldepth"]
        _nodes = info["nodes"] = utils.nodes_to_str(info["nodes"])  # type: str
        _nps = info["nps"] = utils.nodes_to_str(info["nps"])  # type: str
        _time = info["time"]

        board = utils.push_pv(board, pv, info)
        
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
            tb_info = query_tb.query_tablebase(board)
            if tb_info is None:
                print("Tablebase error when fetching eval, stopping!")
                return

            eval_ = tb_info[0]
            dtm = tb_info[1]
            if dtm:
                print(f"Tablebase eval: {eval_} (DTM {dtm})")
            else:
                print(f"Tablebase eval: {eval_}")

            # Get best line (until end of game)
            tb_pv = tb_info[2]
            if tb_pv is None:
                print("Tablebase error when fetching best line, stopping!")
                return

            board = utils.push_pv(board, tb_pv)
            print(f"Traced FEN: {board.fen()}")
            if print_board:
                printBoard.printBoard(board.fen())
                
        if stop_on_tbhit and len(board.piece_map()) <= 7:
            print("Tablebase position reached (<= 7 pieces), stopping!")
            return
        
        
        if utils.is_drawn_score(score):
            drawn_moves_count += 1
        else:
            drawn_moves_count = 0
        
        if stop_on_draw > 0:
            if drawn_moves_count >= stop_on_draw:
                print(f"Drawn for {drawn_moves_count} consecutive iterations, stopping!")
                return
        
        i += 1
        
    
    
def main():
    startfen = input("FEN > ")
    if not startfen:
        startfen = chess.STARTING_FEN
    
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
        stop_on_draw = int(config["STOP_ON_DRAW"])
        
        
    tracePV(startfen, depth=depth, nodes=nodes, time=time, mate=mate, MAX_MOVES=max_moves, MAX_ITER=max_iter,
            print_board=print_board, stop_on_tbhit=stop_on_tbhit, query_on_tbhit=query_on_tbhit, stop_on_draw=stop_on_draw)
    utils.write_pgn()
    
    
    
if __name__ == "__main__":
    main()
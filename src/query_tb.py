import chess
import requests


def query_tablebase_eval(pos: chess.Board):
    """Query the online tablebase for the position.
    :return: TB evaluation, DTM (if applicable)
    """
    """https://github.com/lichess-org/lila-tablebase"""
    
    FEN = pos.fen()
    LINK = "https://tablebase.lichess.ovh/standard?fen=" + FEN
    r = requests.get(LINK, timeout=5)
    j = r.json()
    
    try:
        eval_ = j["category"]  # "win", "loss", "draw", etc.
        dtm_ = j["dtm"] if not eval_ == "draw" else None
    except KeyError:
        return None
    
    return eval_, dtm_
    

def query_tablebase_bestmove(pos: chess.Board):
    """Query the online tablebase for the position.
    :return: best move
    """
    FEN = pos.fen()
    LINK = "https://tablebase.lichess.ovh/standard?fen=" + FEN
    r = requests.get(LINK, timeout=5)
    j = r.json()
    
    try:
        pv = j["moves"]
        return chess.Move.from_uci(pv[0]["uci"])
    except KeyError:
        return None
    

def query_tablebase_pv(board: chess.Board):
    """Query the online tablebase for the position.
    :return: best PV line
    """
    
    # create duplicate board to avoid modifying the original
    pos = board.copy()
    
    pv = []
    while not pos.is_game_over():
        m = query_tablebase_bestmove(pos)
        if m is None:
            return pv
        try:
            pos.push(m)
        except Exception:
            # We may get an AssertionError if checkmate is reached since there is no legal move
            return pv
    
        pv.append(m)
        
    return pv

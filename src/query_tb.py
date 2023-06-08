import chess
import requests


def query_tablebase_eval(pos: chess.Board):
    """Query the online tablebase for the position and return the evaluation."""
    """https://github.com/lichess-org/lila-tablebase"""
    
    FEN = pos.fen()
    LINK = "https://tablebase.lichess.ovh/standard?fen=" + FEN
    r = requests.get(LINK, timeout=10)
    j = r.json()
    
    try:
        eval_ = j["category"]  # "win", "loss", "draw", etc.
        dtm_ = j["dtm"] if not eval_ == "draw" else None
    except KeyError:
        return None
    
    return eval_, dtm_


def query_tablebase_pv(pos: chess.Board):
    """Query the online tablebase for the position and return the best line."""
    
    FEN = pos.fen()
    LINK = "https://tablebase.lichess.ovh/standard/mainline?fen=" + FEN
    r = requests.get(LINK, timeout=10)
    j = r.json()
    
    try:
        pv = j["mainline"]
        pv = [chess.Move.from_uci(d["uci"]) for d in pv]
    except KeyError:
        return None
    
    return pv
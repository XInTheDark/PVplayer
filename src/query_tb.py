import chess
import requests


def query_tablebase(pos: chess.Board):
    """Query the online tablebase for the position.
    :return: TB evaluation + best line
    """
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
    
    pv = []
    try:
        pv = j["moves"]
        pv = [chess.Move.from_uci(d["uci"]) for d in pv]
    except KeyError:
        pv = []
    
    return eval_, dtm_, pv

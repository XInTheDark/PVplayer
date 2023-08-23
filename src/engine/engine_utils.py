import chess, chess.engine
import datetime

def push_pv(board: chess.Board, pv, info=None, is_tb=False):        
    if type(pv) == str:
        pv = pv.split('pv')[-1]
        pv = pv.split()
        
        for move in pv:
            move = chess.Move.from_uci(move)
    
    rule50 = board.halfmove_clock
    for move in pv:        
        board.push(move)
        
        if board.is_game_over(claim_draw=True):
            break
    
    return board


def cp_to_score(cp):
    """@:return: a string of the score in pawn units"""
    if type(cp) == chess.engine.PovScore:
        if cp.is_mate():
            return str(cp.white())
        s = str(cp.white())
        
        if s[0] == '+':
            s = s[1:]
            return f"+{int(s) / 100}"
        elif s[0] == '-':
            s = s[1:]
            return f"-{int(s) / 100}"
        elif s == '0':
            return "0.00"
    elif type(cp) == int:
        if cp == 0:
            return "0.00"
        elif cp > 0:
            return f"+{cp / 100}"
        elif cp < 0:
            return f"{cp / 100}"  # already implied negative sign


def score_to_cp(score):
    """@:return: integer score in centipawns"""
    if type(score) == str:
        if score == "0.00" or score == "0":
            return 0
        if score[0] == '+':
            return int(float(score[1:]) * 100)
        elif score[0] == '-':
            return int(-float(score[1:]) * 100)
        else:
            return score
    elif type(score) == chess.engine.PovScore:
        """if type if PovScore, we also convert to white's POV"""
        return score.white().cp
    

def pv_to_uci(pv):
    s = ""
    for move in pv:
        s += f"{move.uci()} "
    
    # remove the last space
    return s[:-1]
    

def is_drawn_score(score):
    return score == "0.00" or score == "0" or score == 0 or score == chess.engine.Cp(0)


def nodes_to_str(nodes: int):
    """@:return: a string of the number of nodes in millions"""
    return f"{nodes / 1000000:.2f}M"


def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)


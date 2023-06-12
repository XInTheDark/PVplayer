import chess, chess.engine
import datetime
import yaml

ROOT_BOARD = None

PGN_TEXT = f"""[Event "PVplayer analysis"]
[Site "https://github.com/XInTheDark/PVplayer"]
[Date "{datetime.datetime.now().strftime('%Y.%m.%d')}"]
"""
MOVE_COUNT = 1

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)
    export_pgn = config["EXPORT_PGN"]
    detailed_pgn = config["DETAILED_PGN"]


def push_pv(start, pv, info=None, is_tb=False):
    global PGN_TEXT, MOVE_COUNT, ROOT_BOARD
    
    board = None
    if type(start) == str:
        board = chess.Board(start)
    elif type(start) == chess.Board:
        board = start
    
    # Initialise PGN_TEXT if this is the start
    if export_pgn and not "FEN" in PGN_TEXT:
        PGN_TEXT += f"[FEN \"{board.fen()}\"]\n"
    if ROOT_BOARD is None:
        ROOT_BOARD = chess.Board(board.fen())
    
    # Add a note if this is a tablebase PV
    if is_tb:
        PGN_TEXT += "{ Start of tablebase PV } "
    
    if type(pv) == str:
        pv = pv.split('pv')[-1]
        pv = pv.split()
        
        for move in pv:
            move = chess.Move.from_uci(move)
    
    rule50 = board.halfmove_clock
    for move in pv:
        if export_pgn:
            if board.turn == chess.WHITE:
                PGN_TEXT += f"{MOVE_COUNT}. {board.san(move)} "
            else:
                PGN_TEXT += f"{board.san(move)} "
                MOVE_COUNT += 1
        
        board.push(move)
        
        if board.is_game_over(claim_draw=True):
            break
        
        rule50 += 1
        
        # Reset rule50 count because the library implementation is somewhat broken
        if board.is_capture(move):
            rule50 = board.halfmove_clock = 0
        elif board.piece_at(move.from_square).piece_type == chess.PAWN:
            rule50 = board.halfmove_clock = 0
    
    # Append info at end of the current PV iteration in the pgn
    if export_pgn and detailed_pgn and info is not None:
        PGN_TEXT += f"{{ {info['score']}, depth {info['depth']}/{info['seldepth']}," \
                    f" {info['nodes']} nodes }} "
    
    # Correct the rule50 count in FEN
    f = board.fen().split()
    f[-2] = str(rule50)
    f = ' '.join(f)
    
    ROOT_BOARD = board
    
    return chess.Board(f)


def write_pgn():
    """Write the saved PGN into the /PVplayer/pgns directory (create it if it doesn't exist)"""
    global PGN_TEXT
    
    if not export_pgn:
        return
    
    print("Writing PGN...")
    
    # Create the directory if it doesn't exist
    import os
    os.chdir("..")
    if not os.path.exists("pgns"):
        os.mkdir("pgns")
    
    # Write the PGN
    with open(f"pgns/{datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S')}.pgn", "w") as f:
        f.write(PGN_TEXT)
    
    # Reset PGN_TEXT
    PGN_TEXT = f"""[Event "PVplayer analysis"]
    [Site "https://github.com/XInTheDark/PVplayer"]
    [Date "{datetime.datetime.now().strftime('%Y.%m.%d')}"]
    """
    
    print("PGN written to /pgns!")


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
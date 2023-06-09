import chess, chess.engine
import datetime
import yaml

PGN_TEXT = f"""[Event "PVplayer analysis"]
[Site "https://github.com/XInTheDark/PVplayer"]
[Date "{datetime.datetime.now().strftime('%Y.%m.%d')}"]
"""
MOVE_COUNT = 1

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)
    export_pgn = config["EXPORT_PGN"]
    detailed_pgn = config["DETAILED_PGN"]


def push_pv(start, pv, info=None):
    global PGN_TEXT, MOVE_COUNT
    
    board = None
    if type(start) == str:
        board = chess.Board(start)
    elif type(start) == chess.Board:
        board = start

    # Initialise PGN_TEXT if this is the start
    if export_pgn and not "FEN" in PGN_TEXT:
        PGN_TEXT += f"[FEN \"{board.fen()}\"]\n"
    
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
        rule50 += 1
        
        # Reset rule50 count because the library implementation is somewhat broken
        if board.is_capture(move):
            rule50 = board._halfmove_clock = 0
        elif board.piece_at(move.from_square).piece_type == chess.PAWN:
            rule50 = board._halfmove_clock = 0
            
    # Append info at end of the current PV iteration in the pgn
    if export_pgn and detailed_pgn and info is not None:
        PGN_TEXT += f"{{ {info['score']}, depth {info['depth']}/{info['seldepth']}," \
                    f" {info['nodes']} nodes }} "
        
    # Correct the rule50 count in FEN
    f = board.fen().split()
    f[-2] = str(rule50)
    f = ' '.join(f)
    
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


def cp_to_score(cp: chess.engine.PovScore):
    """@:return: a string of the score in pawn units"""
    if cp.is_mate():
        return str(cp)
    s = str(cp.white())

    if s[0] == '+':
        s = s[1:]
        return f"+{int(s) / 100}"
    elif s[0] == '-':
        s = s[1:]
        return f"-{int(s) / 100}"
    elif s == '0':
        return "0.00"
    
    
def nodes_to_str(nodes: int):
    """@:return: a string of the number of nodes in millions"""
    return f"{nodes / 1000000:.2f}M"
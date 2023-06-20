import chess

import utils
import datetime
import os

"""A small utility to convert UCI PV to a PGN file."""


def uci_to_pgn(start_fen: str, uci_pv: str):
    board = chess.Board(start_fen)
    pv = uci_pv.split()
    pgn = f"""[Event "PVplayer UCI to PGN utility"]
[Site "https://github.com/XInTheDark/PVplayer"]
[Date "{datetime.datetime.now().strftime('%Y.%m.%d')}"]
[FEN "{start_fen}"]
"""
    
    MOVE_COUNT = board.fullmove_number
    
    for move in pv:
        move = chess.Move.from_uci(move)
        if board.turn == chess.WHITE:
            pgn += f"{MOVE_COUNT}. {board.san(move)} "
        else:
            pgn += f"{board.san(move)} "
            MOVE_COUNT += 1
        board.push(move)
        
    # Write to /pgns (create if it doesn't exist)
    os.chdir("..")
    if not os.path.exists("pgns"):
        os.mkdir("pgns")
        
    FILE_NAME = f"pgns/{datetime.datetime.now().strftime('uci_to_pgn %Y.%m.%d %H.%M.%S')}.pgn"
    with open(FILE_NAME, "w") as f:
        f.write(pgn)
        
    print(f"PGN written to {FILE_NAME}")


if __name__ == "__main__":
    start_fen = input("FEN > ")
    if not start_fen:
        start_fen = chess.STARTING_FEN
    
    uci_pv = input("UCI PV > ")
    
    uci_to_pgn(start_fen, uci_pv)
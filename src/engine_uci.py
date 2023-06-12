"""
Special thanks to PyFish for most of the UCI code.
"""

import chess, chess.engine

import engine_search
from engine_ucioption import *


# constants
MAX_DEPTH = 100

def move_to_uci(move: chess.Move):
    """Convert a chess.Move object to a UCI string."""
    return move.uci()


def uci_to_move(s: str):
    """Convert a UCI string to a chess.Move object."""
    return chess.Move.from_uci(s)


def fen_from_str(s: str):
    """Parse the FEN from a string.
    For example, input: '3R4/r7/3k2P1/3p4/2pP4/1b2PK1N/5P2/8 b - - 3 48 moves d6g7',
    output: ['3R4/r7/3k2P1/3p4/2pP4/1b2PK1N/5P2/8 b - - 3 48', 'moves d6g7']
    where the first element in the list is the FEN and the remaining is the rest of the string.
    """
    
    l = s.split(" ")
    if len(l) < 6:
        raise ValueError("Invalid FEN")
    
    fen = " ".join(l[:6])
    rest = " ".join(l[6:])
    
    return [fen, rest]


def uci():
    """
    Start the UCI interface.
    """
    
    print("PVplayer chess engine")
    pos = chess.Board()
    while True:
        command = input()
        if command == "uci":
            print(f"id name PVplayer")
            print(f"id author the PVplayer developers (see AUTHORS file)\n")
            # UCI options
            print(options_str())
            print("uciok")
        elif command == "isready":
            print("readyok")
        elif command == "ucinewgame":
            pos = chess.Board()
        elif command == "position startpos":
            pos = chess.Board()
        elif command.startswith("position startpos moves"):
            try:
                moves = command.split("position startpos moves ")[1].split(" ")
            except IndexError:
                moves = []
            for move in moves:
                pos.push(uci_to_move(move))
        elif command.startswith("position fen") and "moves" in command:
            # remove 'position fen '
            s = ' '.join(command.split(" ")[2:])
            fen = fen_from_str(s)[0]
            moves = fen_from_str(s)[1].split()[1:]
            pos = chess.Board(fen)
            for move in moves:
                pos.push(uci_to_move(move))
        elif command.startswith("position fen"):
            s = ' '.join(command.split(" ")[2:])
            fen = fen_from_str(s)[0]
            pos = chess.Board(fen)
        elif command.startswith("go"):
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "movetime":
                movetime = int(command.split(" ")[2])
            else:
                movetime = None
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "nodes":
                nodes = int(command.split(" ")[2])
            else:
                nodes = None
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "depth":
                MAX_ITERS = int(command.split(" ")[2])
            else:
                MAX_ITERS = MAX_DEPTH
            
            if command.split(" ").__len__() > 1 and command.split(" ")[1] == "infinite":
                MAX_ITERS = MAX_DEPTH
            
            # we do not support time controls yet.
            # we also do not support pondering.
            
            # start searching
            engine_search.search(pos, MAX_MOVES=option("MAX_MOVES"), MAX_ITERS=MAX_ITERS, time=movetime, nodes=nodes)
            
        # TODO: quit and stop

        # option setting
        elif command.startswith("setoption"):
            # FORMAT: name <id> value <x>
            c = command.split()
            if not c[1] == "name":
                continue
            try:
                value_index = c.index("value")
            except ValueError:
                # Type = button
                value_index = c.__len__()
            name = " ".join(c[2:value_index])
            value = " ".join(c[value_index + 1:])
    
            # set the option
            setoption(name, value)
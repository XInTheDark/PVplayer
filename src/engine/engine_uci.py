"""
Special thanks to PyFish for most of the UCI code.
"""

import chess, chess.engine

import engine_search
from engine_ucioption import *
from engine_utils import *
from engine_timeman import Time
from engine_engine import engine

import threading, sys, atexit, os


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


def handle_commands():
    pos = chess.Board()
    search_thread = None
    
    try:
        while True:
            try:
                command = preprocess(sys.stdin.readline())
            except Exception:
                continue
                
            printf(f"uciinput: {command}")
                
            tm = Time()  # initialize new timeman object
            
            if command == "uci":
                printf(f"id name PVplayer")
                printf(f"id author the PVplayer developers (see AUTHORS file)\n")
                # UCI options
                printf(options_str())
                printf("uciok")
            elif command == "isready":
                printf("readyok")
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
                MAX_ITERS = MAX_DEPTH
                
                if command.strip() == "go":
                    MAX_ITERS = 10
                    
                has_arg = command.split(" ").__len__() > 1
                args = command.split(" ")
                keyword = command.split(" ")[1] if has_arg else None
                
                if has_arg and keyword == "movetime":
                    movetime = int(command.split(" ")[2])
                else:
                    movetime = None
                
                if has_arg and keyword == "nodes":
                    nodes = int(command.split(" ")[2])
                else:
                    nodes = None
                
                if has_arg and keyword == "depth":
                    MAX_ITERS = int(command.split(" ")[2])
                
                if has_arg and keyword == "infinite":
                    MAX_ITERS = MAX_DEPTH
                
                if has_arg and ("wtime" in args or "btime" in args):
                    wtime, btime, winc, binc = process_time(args)
                    tm.__init__(wtime, btime, winc, binc)
                    
                # we do not support time controls yet.
                # we also do not support pondering.
                
                # start search
                search_thread = threading.Thread(target=start_search, args=(pos, option("MAX_MOVES"), MAX_ITERS,
                                                                            movetime, nodes, tm))
                search_thread.start()
                
            # stop
            elif command == "stop":
                if search_thread:
                    engine_search.stop_search()
                    search_thread.join(timeout=0.5)
                    search_thread = None
            # quit
            elif command == "quit":
                if search_thread:
                    engine_search.stop_search()
                    search_thread.join(timeout=0.5)
                os._exit(0)
            
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
    except KeyboardInterrupt:
        exit()
        

def start_search(pos, MAX_MOVES, MAX_ITERS, time, nodes, tm):
    engine_search.search(pos, MAX_MOVES=MAX_MOVES, MAX_ITERS=MAX_ITERS, movetime=time, nodes=nodes, timeman=tm)
    
    
def uci():
    """
    Start the UCI interface.
    """
    log_file(True)
    printf("PVplayer chess engine")
    
    # Create a thread for handling UCI input
    uci_thread = threading.Thread(target=handle_commands)
    uci_thread.start()
        
        
# Helper functions
def process_time(args: list):
    wtime = btime = winc = binc = 0
    try:
        wtime = int(args[args.index("wtime") + 1])
    except ValueError:
        pass
    
    try:
        btime = int(args[args.index("btime") + 1])
    except ValueError:
        pass
    
    try:
        winc = int(args[args.index("winc") + 1])
    except ValueError:
        pass
    
    try:
        binc = int(args[args.index("binc") + 1])
    except ValueError:
        pass
    
    return wtime, btime, winc, binc

def preprocess(s: str):
    s = s.strip()
    l = []
    for chunk in s.split():
        chunk = chunk.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
        if chunk != "":
            l.append(chunk)
    return ' '.join(l)


@atexit.register
def on_exit():
    engine_search.stop_search()
    if engine is not None:
        engine.quit()
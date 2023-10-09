"""
Special thanks to PyFish for most of the UCI code.
"""
ENGINE_VERSION = "v5.0.0"
ENGINE_NAME = "PVengine"
ENGINE_AUTHOR = "J Muzhen"

import atexit
import os
import sys
import threading

import chess.engine

import search
from evaluate import engine
from timeman import Time
from utils import *
from search_h import *
from benchmark import bench

# threads
search_thread = None

pos = chess.Board()
tm = Time()


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

    if "moves" in s:
        s = s.split(" moves ")
        fen = s[0]
        moves = s[1]
    else:
        fen = s
        moves = ""

    return [fen, moves]


def handle_command(command: str):
    global search_thread, pos, tm
    command = preprocess(command)
    if command == "":
        return
    search_thread = None

    tm = Time()  # initialize new timeman object

    if command == "uci":
        printf(f"id name {ENGINE_NAME}")
        printf(f"id author {ENGINE_AUTHOR}")
        # UCI options
        printf(options_str())
        printf("uciok")
    elif command == "isready":
        printf("readyok")
    elif command == "ucinewgame":
        pos = chess.Board()
        tm = Time()
    elif command == "position startpos":
        pos = chess.Board()
    elif command.startswith("position startpos moves"):
        pos = chess.Board()
        try:
            moves = command.split(" ")[3:]
        except IndexError:
            moves = []
        for move in moves:
            move = uci_to_move(move)
            if not pos.is_legal(move):
                break
            pos.push(move)
    elif command.startswith("position fen") and "moves" in command:
        # remove 'position fen '
        s = ' '.join(command.split(" ")[2:])
        obj = fen_from_str(s)
        fen = obj[0]
        moves = obj[1].split()
        pos = chess.Board(fen)
        for move in moves:
            move = uci_to_move(move)
            if not pos.is_legal(move):
                break
            pos.push(move)
    elif command.startswith("position fen"):
        s = ' '.join(command.split(" ")[2:])
        fen = fen_from_str(s)[0]
        pos = chess.Board(fen)
    elif command.startswith("go"):
        MAX_ITERS = GET_MAX_DEPTH()

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
            MAX_ITERS = GET_MAX_DEPTH()

        if has_arg and ("wtime" in args or "btime" in args):
            wtime, btime, winc, binc = process_time(args)
            tm.__init__(wtime, btime, winc, binc)

        # start search
        search_thread = threading.Thread(target=start_search, args=(pos, option("MAX_MOVES"), MAX_ITERS,
                                                                    movetime, nodes, tm))
        search_thread.start()

    # stop
    elif command == "stop":
        search.stop_search()
        if search_thread:
            search_thread.join(timeout=0.5)
            search_thread = None

    # quit
    elif command == "quit":
        if search_thread:
            search.stop_search()
            search_thread.join(timeout=0.5)
        os._exit(0)

    # bench
    elif command.startswith("bench"):
        try:
            depth = int(command.split(" ")[1])
        except Exception:
            depth = 3
        bench(depth)

    # option setting
    elif command.startswith("setoption"):
        # FORMAT: name <id> value <x>
        c = command.split()
        if not c[1] == "name":
            printf("No such option: ")
            return
        try:
            value_index = c.index("value")
        except ValueError:
            # Type = button
            value_index = c.__len__()
        name = " ".join(c[2:value_index])
        value = " ".join(c[value_index + 1:])

        # set the option
        try:
            setoption(name, value)
        except KeyError:
            printf(f"No such option: '{name}'. Type 'uci' for all options.")
        except Exception as e:
            printf(f"Failed to set option: '{name}'. Error: {e}")

    elif command == "d":
        printf(pos.__str__() + "\n")
        printf(f"FEN: {pos.fen()}")
        printf(f"Checkers: {','.join([chess.square_name(sq) for sq in pos.checkers()])}")

    else:
        printf(f"Unknown command: '{command}'.")
        return


def handle_commands():
    global search_thread, pos, tm
    pos = chess.Board()
    tm = Time()
    if len(sys.argv) > 1:
        # split when there is a newline
        lst = ' '.join(sys.argv[1:]).split("\n")
        for command in lst:
            handle_command(command)
        while search.IS_SEARCHING:
            continue
        os._exit(0)

    while True:
        try:
            command = preprocess(sys.stdin.readline())
            handle_command(command)
        except Exception:
            continue


def start_search(pos, MAX_MOVES, MAX_ITERS, time, nodes, tm):
    while search.IS_SEARCHING:
        continue

    search.search(pos, MAX_MOVES=MAX_MOVES, MAX_ITERS=MAX_ITERS, movetime=time, nodes=nodes, timeman=tm)


def uci():
    """
    Start the UCI interface.
    """
    global ENGINE_NAME
    ENGINE_NAME = engine_name_uci()
    printf(f"{ENGINE_NAME} by {ENGINE_AUTHOR}")

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


def engine_name_uci():
    if ENGINE_VERSION:
        text = f"PVengine {ENGINE_VERSION}"
    else:
        text = "PVengine"
    return text


@atexit.register
def on_exit():
    search.stop_search()
    if engine is not None:
        engine.quit()

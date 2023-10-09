import search
import chess
import time, os
import timeman


def bench(depth: int = 3):
    # Run search on startpos
    pos = chess.Board()
    start = time.time()
    print("go depth", depth)
    search.search(pos, MAX_ITERS=depth)

    # Run movetime 10000
    print("go movetime 10000")
    search.search(pos, movetime=10000)

    # Run nodes 2000000
    print("go nodes 2000000")
    search.search(pos, nodes=2000000)

    # Run wtime 60000 winc 1000
    print("go wtime 60000 winc 1000 btime 60000 binc 1000")
    tm = timeman.Time(60000, 60000, 1000, 1000)
    search.search(pos, timeman=tm)

    end = time.time()
    print("Time taken:", round(end - start, 2), "seconds")

    # Quit
    os._exit(0)

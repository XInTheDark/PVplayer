import chess, chess.engine

import engine_engine
import utils
from engine_search_h import *
from engine_ucioption import *
from engine_timeman import *

from time import time as time_now
import threading
import math

STOP_SEARCH = OPTTIME = MAXTIME = False

lastNps = 1000000 * option("Threads")

def search(rootPos: chess.Board, MAX_MOVES=5, MAX_ITERS=5, depth: int = None, nodes: int = None, time: int = None,
            mate: int = None, timeman: Time = Time()):
    """
    Search a position by tracing the PV.
    
    param depth: Maximum number of iterations
    param nodes: Maximum number of *total* nodes across all iterations
    param time: Maximum time *per move*
    """
    
    global STOP_SEARCH, lastNps
    global OPTTIME, MAXTIME

    # initialise timeman object
    timeman.init(rootPos.turn, rootPos.ply())
    optTime = timeman.optTime
    maxTime = timeman.maxTime

    startTime = time_now()
    optTime_timer = maxTime_timer = None
    
    # Set timer
    if optTime:
        optTime_timer = threading.Timer(optTime / 1000, stop_search, args=(True, False))
        optTime_timer.start()
        if option("debug"):
            print(f"info string Timeman: Optimal time {optTime}ms")
    if maxTime:
        maxTime_timer = threading.Timer(maxTime / 1000, stop_search, args=(True, True))
        maxTime_timer.start()
    
    i = 1
    total_nodes = 0
    
    default_nodes = option("Nodes")
    
    rootMoves = list(rootPos.legal_moves)
    rootMovesSize = len(list(rootMoves))
    
    # If we likely don't have enough time to search all moves, only use root engine eval
    if optTime:
        if rootMovesSize * default_nodes > optTime / 1000 * lastNps:
            info: chess.engine.InfoDict = engine_engine.__engine__(fen=rootPos.fen(), time=optTime / 1000)
            score = Value(info["score"])
            bestPv = info["pv"]
            bestMove = bestPv[0]
            
            print(f"info depth 0 seldepth {info['depth']} score cp {score.__uci_str__()} nodes {info['nodes']} nps {info['nps']} "
                  f"time {int(info['time'] * 1000)} pv {utils.pv_to_uci(bestPv)}")
            if len(bestPv) <= 1:
                print(f"bestmove {bestMove}")
            else:
                print(f"bestmove {bestMove} ponder {bestPv[1]}")
            return
            
            
    info: chess.engine.InfoDict = engine_engine.__engine__(fen=rootPos.fen(), depth=depth, nodes=default_nodes, time=time,
                                                    mate=mate)
    
    rootScore = Value(info["score"])
    rootBestMove = info["pv"][0]
    rootPv = info["pv"]
    total_nodes += info["nodes"]
    
    print(f"info depth 0 seldepth {info['depth']} score cp {rootScore.__uci_str__()} nodes {total_nodes} nps {info['nps']} "
          f"pv {utils.pv_to_uci(rootPv)}")
    rootStm = rootPos.turn
    
    
    # initialise dictionary for current position after each root move
    # key: root move, value: position
    rootMovesPos = {}
    rootMovesDepth = {}
    rootMovesEval = {}
    rootMovesPv = {}
    pruned_rootMoves = {}
    rootMovesExtraNodes = {}
    
    bestValue = Value(-VALUE_INFINITE, rootStm)
    bestMove = None
    bestMoveChanges = 0
    prevBestValue = rootScore
    prevBestMove = rootBestMove
    
    root_time = last_output_time = time_now()
    
    while i <= MAX_ITERS:
        # Pre-iteration check:
        # If we estimate that this iteration will take too long,
        # Then we should stop searching in order to save time in timed games.
        if optTime:
            # Estimate total nodes based on rootMovesSize
            if rootMovesSize * default_nodes > optTime / 1000 * lastNps:
                if not bestMove:
                    bestMove = rootBestMove
                try:
                    ponderMove = rootMovesPv[bestMove][1]
                except KeyError:
                    ponderMove = None
                if ponderMove:
                    print(f"bestmove {bestMove} ponder {ponderMove}")
                else:
                    print(f"bestmove {bestMove}")
                    
                if option("debug"):
                    print(f"info string Timeman: Early abort")
                return
            
        # Time management
        # Use more time if bestMove is unstable
        if optTime:
            optTime *= (1 + 1.5 * math.log10(bestMoveChanges))
            # reset timer
            optTime_timer.cancel()
            optTime_timer = threading.Timer(optTime / 1000, stop_search, args=(True, False))
            optTime_timer.start()
            
        
        for move in rootMoves:
            # Check for stopped search
            if STOP_SEARCH or (nodes and total_nodes >= nodes):
                # Timeman: if optTime has been reached but we are almost done
                # (i.e. we can finish this iteration within maxTime)
                # then we continue searching until we finish this iteration.
                # However, estimate a bit more conservatively to avoid wasting time.
                if OPTTIME and not MAXTIME:
                    move_i = rootMoves.index(move)+1
                    if (rootMovesSize - move_i) * default_nodes * 1.2 < maxTime / 1000 * lastNps:
                        if option("debug"):
                            print(f"info string Timeman: Extra time")
                        continue
                
                STOP_SEARCH = OPTTIME = MAXTIME = False  # reset
                
                # Use previous iteration best move since this iteration is incomplete
                bestMove = prevBestMove
                bestValue = prevBestValue
                    
                try:
                    bestPv = rootMovesPv[bestMove]
                except KeyError:
                    bestPv = [bestMove]

                time_taken = time_now() - root_time
                print(f"info depth {i} score cp {bestValue.__uci_str__()} nodes {total_nodes} nps {int(total_nodes / time_taken)} "
                      f"time {int(time_taken * 1000)} pv {utils.pv_to_uci(bestPv)}")
                
                
                if len(bestPv) <= 1:
                    print(f"bestmove {bestMove}")
                else:
                    print(f"bestmove {bestMove} ponder {bestPv[1]}")
                return
                
            if move in pruned_rootMoves.keys():
                pruned_iter = pruned_rootMoves[move]
                if pruned_iter > 2 or pruned_iter >= i - 5:
                    # if it is pruned late, then we can assume that it is a bad move
                    continue
                else:
                    if i - pruned_iter >= 2:
                        pruned_rootMoves.pop(move)
            
            # find position in rootMovesPos: almost like a transposition table, but not quite.
            # if move is found, then we can continue searching from where we left off.
            if move in rootMovesPos.keys():
                pos = rootMovesPos[move]
            else:
                pos = rootPos.copy()
                pos.push(move)
                rootMovesPos[move] = pos
            
            # UCI: if there hasn't been an output for 5 seconds, output currmove
            if time_now() - last_output_time >= 5:
                print(f"info depth {i} currmove {move} currmovenumber {rootMoves.index(move) + 1} "
                      f"nodes {total_nodes}")
                last_output_time = time_now()
                
            # search
            try:
                prevEval = rootMovesEval[move]
            except KeyError:
                prevEval = None
                
            move_nodes = calc_nodes(move, bestValue, i, default_nodes, prevEval, (move==bestMove), rootMovesExtraNodes)
            
            info: chess.engine.InfoDict = engine_engine.__engine__(fen=pos.fen(), depth=depth, nodes=move_nodes, time=time,
                                                            mate=mate)
            total_nodes += info["nodes"]
            lastNps = info["nps"]
            pv = info["pv"]
            pv = pv[:MAX_MOVES]
            
            if move not in rootMovesPv.keys():
                rootMovesPv[move] = [move]
                rootMovesPv[move].extend(pv)
            else:
                rootMovesPv[move].extend(pv)
            
            depth = info["depth"]
            if depth not in rootMovesDepth.keys():
                rootMovesDepth[move] = depth
            
            value = Value(info["score"], rootStm)

            # update rootMovesEval
            rootMovesEval[move] = value
            
            if option("debug"):
                print(f"info string Iteration {i} | Move: {move} | Eval: {value}")
            
            rootMovesPos[move] = pos = utils.push_pv(pos, pv, info)
            
            if value > bestValue:
                if move != bestMove:
                    bestMoveChanges += 1
                bestValue = value
                bestMove = move
                
        # print(f"Iteration {i} | Best move: {bestMove} | Eval: {bestValue} | Depth: {depth}")
        
        # proper UCI formatting
        time_taken = time_now() - root_time
        print(f"info depth {i} seldepth {depth} score cp {bestValue.__uci_str__()} nodes {total_nodes} nps {int(total_nodes / time_taken)} "
              f"time {int(time_taken * 1000)} pv {utils.pv_to_uci(rootMovesPv[bestMove])}")
        
        # Update pruned moves after we finish searching all root moves
        for move in rootMovesEval.keys():
            v = rootMovesEval[move]
            min_prune_eval = prune_margin(bestValue, i)
            if v < min_prune_eval:
                pruned_rootMoves[move] = i
                if option("debug"):
                    print(f"info string Iteration {i} | Pruned: {move} | Prune margin: {min_prune_eval}")
                
        # Update moves list size
        rootMovesSize = [1 for m in rootMoves if m not in pruned_rootMoves.keys()].__len__()
        
        if rootMovesSize / len(rootMoves) < 0.2:
            # Extreme case: only few moves remains after pruning
            
            # Give extra nodes to the best move
            if bestMove not in rootMovesExtraNodes.keys():
                rootMovesExtraNodes[bestMove] = 1.2  # initial bonus multiplier
            else:
                rootMovesExtraNodes[bestMove] *= 1.25
            
            # Allow re-calculation of move PVs
            for m in rootMovesPv.keys():
                # Delete the end of the PV, depending on how promising the move is.
                # The more promising it is, the more we delete to allow more accurate calculation.
                p = promising(m, rootMovesEval, rootMovesSize, i, (m == bestMove),
                              bestValue) # float from 0 to 1
                p = min(p, 0.8)
                
                # Extra bonus if PV is long
                p += len(rootMovesPv[m]) / 250
                # allow deletion of the entire PV only if i >= 10
                p = min(min(p, 0.9 + i / 100), 1.0)
                
                # delete PV
                del_moves = int(len(rootMovesPv[m]) * p)
                del_moves = max(del_moves, 1)  # cannot delete root move
                rootMovesPv[m] = rootMovesPv[m][:del_moves]
                
                # update position
                rootMovesPos[m] = utils.push_pv(rootPos.copy(), rootMovesPv[m])
                
            # Restart the search
            rootMovesSize = len(list(rootMoves))
            pruned_rootMoves = {}
            prevBestValue = bestValue
            prevBestMove = bestMove
            bestValue = Value(-VALUE_INFINITE, rootStm)
            
        i += 1
        
    # After search is finished
    bestPv = rootMovesPv[bestMove]
    if len(bestPv) == 1:
        print(f"bestmove {bestMove}")
    else:
        print(f"bestmove {bestMove} ponder {bestPv[1]}")
        
        
def prune_margin(bestValue: Value, i: int):
    """
    Prune the root moves that return an eval below the margin.
    """
    
    bestValue = int(bestValue)
    
    m = float(bestValue - 50)
    # Be more lenient with the margin for the first few iterations
    m += (3 - i) * (20 if i < 3 else 10)
    
    # Scale on bestValue: if the absolute value is large we prune more aggressively
    m -= abs(bestValue) / 10 if abs(bestValue) >= 50 else 0
    
    # If abs(bestValue) is small, then we prune less aggressively
    m += abs(bestValue) / 2.5 if abs(bestValue) < 75 else 0
    
    # if bestValue is positive, then we allow only positive evals
    if bestValue > 0:
        smallest_allow = -25 + bestValue / 2
        smallest_allow = min(smallest_allow, 0)
        m = max(m, smallest_allow)
    
    m = int(m)
    return min(m, bestValue - 10)
    

def calc_nodes(move: chess.Move, bestValue: Value, i: int, default_nodes: int, prevEval
               , is_best: bool, rootMovesExtraNodes: dict):
    """
    Calculate the number of nodes to search, based on search heuristics.
    """
    
    bestValue = int(bestValue)
    prevEval = int(prevEval) if prevEval is not None else None
    scale = 1.0
    
    # If best move, search 30% more nodes
    if is_best or (prevEval and prevEval >= bestValue):
        scale *= 1.3
        
    # Use more nodes for the first few iterations (also important for accuracy in pruning)
    if i <= 3:
        if not prevEval:
            scale *= 1.5
        else:
            scoreDiff = max(bestValue - prevEval, 0)
            scale *= clamp(1.5 - (scoreDiff / 250), 1.05, 1.4)
        
    
    # # if prevEval is close to bestValue then search some more nodes depending on rootMovesSize
    # if prevEval >= bestValue - 20:
    #     scale = min(1.05, 1 + ((40 - rootMovesSize) / 100))
    # overriden by promising()
        
    if move in rootMovesExtraNodes.keys():
        scale *= rootMovesExtraNodes[move]
    
    return int(default_nodes * scale)

    
def promising(move: chess.Move, rootMovesEval: dict, rootMovesSize: int, i: int, is_best: bool,
              bestValue: Value):
    """
    Return a float from 0 to 1, indicating how promising a move is.
    """
    
    # If best move, return 1
    if is_best:
        return 1.0
    
    # Scale according to how much worse than bestValue eval is
    ev = rootMovesEval[move]
    eval_score = 1.0 - (bestValue - ev) / 200
    eval_score = clamp(eval_score, 0.01, 1.0)
    
    # Scale according to iteration (the greater the iteration, the stricter we are)
    iter_score = clamp(1.2 - (i / 20), 0.5, 1.2)
    
    # Scale according to rootMovesSize
    size_score = clamp(1.1 - (rootMovesSize / 40), 0.75, 1.0)
    
    final_score = clamp(eval_score * iter_score * size_score, 0.0, 1.0)
    
    return final_score
    
    
def stop_search(optTime=False, maxTime=False):
    global STOP_SEARCH, OPTTIME, MAXTIME
    STOP_SEARCH = True
    
    if optTime:
        OPTTIME = True
    if maxTime:
        MAXTIME = True

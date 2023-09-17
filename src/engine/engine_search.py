from time import time as time_now

import chess.engine

import engine_engine
from engine_engine import __engine__, init_engine
from engine_search_h import *
from engine_timeman import *
from engine_utils import printf

STOP_SEARCH = OPTTIME = MAXTIME = False
IS_SEARCHING = False

npsAverage = RunningAverage(max_count=5)


def search(rootPos: chess.Board, MAX_MOVES=GET_MAX_MOVES(), MAX_ITERS=GET_MAX_DEPTH(),
           depth: int = None, nodes: int = None, movetime: int = None,
           timeman: Time = Time()):
    """
    Search a position by tracing the PV.
    
    param depth: Maximum number of iterations
    param nodes: Maximum number of *total* nodes across all iterations
    param time: Maximum time *per move*
    """
    
    global STOP_SEARCH, npsAverage, IS_SEARCHING
    global OPTTIME, MAXTIME
    
    STOP_SEARCH = False
    IS_SEARCHING = True
    
    # start timer immediately for accuracy
    root_time = last_output_time = time_now()
    
    # initialise timeman object
    timeman.init(rootPos.turn, rootPos.ply())
    optTime = timeman.optTime
    optTimeLeft = optTime
    maxTime = timeman.maxTime
    if movetime:
        optTime = maxTime = movetime
        
    useTimeMan = optTime or maxTime
    startTime = time_now()
    
    if optTime:
        if option("debug"):
            printf(f"info string Timeman: Optimal time {optTime}ms")
    if maxTime:
        if option("debug"):
            printf(f"info string Timeman: Maximum time {maxTime}ms")
    
    # Initialise engine if not already initialised
    if not engine_is_alive():
        init_engine()
    
    i = 1
    total_nodes = 0
    npsAverage.clear()
    default_nodes = setNodes(option("Nodes"), i)
    
    rootMoves = list(rootPos.legal_moves)
    rootMovesSize = len(list(rootMoves))
    
    # Handle illegal moves
    if rootMovesSize == 0 or not rootPos.is_valid():
        printf("bestmove (none)")
        IS_SEARCHING = False
        return
    
    # If we likely don't have enough time to search all moves, only use root engine eval
    if useTimeMan:
        # Special case: When we are under time control, and only one legal move, return immediately
        if rootMovesSize == 1:
            bestMove = rootMoves[0]
            printf(f"info depth 0 nodes 0 time 0 pv {bestMove}")
            printf(f"bestmove {bestMove}")
            IS_SEARCHING = False
            return
        
        if rootMovesSize * default_nodes > optTime / 1000 * Nps():
            # use the engine's timeman
            info: chess.engine.InfoDict = __engine__(pos=rootPos, timeMan=timeman)
            score = Value(info["score"])
            bestPv = info["pv"]
            bestMove = bestPv[0]
            
            printf(
                f"info depth 0 seldepth {info['depth']} score cp {score.__uci_str__()} nodes {info['nodes']} nps {info['nps']} "
                f"time {int(info['time'] * 1000)} pv {utils.pv_to_uci(bestPv)}")
            if len(bestPv) <= 1:
                printf(f"bestmove {bestMove}")
            else:
                printf(f"bestmove {bestMove} ponder {bestPv[1]}")
            IS_SEARCHING = False
            return
    
    info: chess.engine.InfoDict
    if option("Nodes") != "auto":
        info = __engine__(pos=rootPos, nodes=default_nodes)
    else:
        info = __engine__(pos=rootPos, movetime=1.0)
        
    
    rootScore = Value(info["score"])
    rootBestMove = info["pv"][0]
    rootPv = info["pv"]
    total_nodes += info["nodes"]
    npsAverage.add(info["nps"])
    
    printf(
        f"info depth 0 seldepth {info['depth']} score cp {rootScore.__uci_str__()} nodes {total_nodes} nps {Nps()} "
        f"time {int(info['time'] * 1000)} pv {utils.pv_to_uci(rootPv)}")
    
    rootStm = rootPos.turn
    
    # initialise dictionary for current position after each root move
    # key: root move, value: position
    rootMovesPos = {}
    rootMovesDepth = {}
    rootMovesEval = {}
    rootMovesPv = {}
    pruned_rootMoves = {}
    rootMovesExtraNodes = {}
    
    nextIterRecalcMoves = []  # list of root moves that need to be recalculated next iter
    
    bestValue = Value(-VALUE_INFINITE, rootStm)
    bestMove = rootBestMove  # in case we have no time to search, at least return a move
    bestMoveChanges = 0
    prevBestValue = rootScore
    prevBestMove = rootBestMove
    prevRecalcIter = -1
    recalcCount = 0
    
    extraTimeIter = 0  # the iteration where we start using extra time
    
    while i <= MAX_ITERS:
        # Pre-iteration check:
        # If we estimate that this iteration will take too long,
        # Then we should stop searching in order to save time in timed games.
        if useTimeMan:
            # Estimate total nodes based on rootMovesSize
            # Be relatively more aggressive as we can always stop later
            if rootMovesSize * default_nodes > optTimeLeft / 1000 * Nps() * 2:
                if not bestMove:
                    bestMove = rootBestMove
                try:
                    ponderMove = rootMovesPv[bestMove][1]
                except Exception:  # KeyError, IndexError, etc
                    ponderMove = None
                if ponderMove:
                    printf(f"bestmove {bestMove} ponder {ponderMove}")
                else:
                    printf(f"bestmove {bestMove}")
                
                if option("debug"):
                    printf(f"info string Timeman: Early abort")
                IS_SEARCHING = False
                return
        
        # Increase default_nodes as iteration increases
        default_nodes *= 1.0 + max(0.0, (0.0025 - 0.000033 * i) * i)
        default_nodes = min(default_nodes, 10 * setNodes(option("Nodes"), i))  # cap at 10x default
        if option("debug"):
            print(f"info string default_nodes: {default_nodes}")

        # Use more time for this iteration if bestMove is unstable
        if bestMoveChanges > 0:
            bestMoveInstability = 0.8 + 1.5 * math.log10(bestMoveChanges + 1) / option("Threads")
            optTime = optTime * bestMoveInstability
            if option("debug"):
                printf(f"info string Timeman: bestMoveChanges {bestMoveChanges}, scale {bestMoveInstability}")
        
        # reset constants
        bestMoveChanges = 0
        
        # moves loop
        for move in rootMoves:
            # Update time management
            elapsed_total = (time_now() - startTime) * 1000
            optTimeLeft = optTime - elapsed_total
            
            OPTTIME = useTimeMan and (OPTTIME or (optTimeLeft and optTimeLeft <= 0))
            MAXTIME = useTimeMan and (MAXTIME or (maxTime and elapsed_total >= maxTime))
            STOP_SEARCH = STOP_SEARCH or OPTTIME or MAXTIME
            NODES_LIMIT_REACHED = nodes and total_nodes >= nodes
            
            if STOP_SEARCH or NODES_LIMIT_REACHED:
                # Timeman: if optTime has been reached but we are almost done
                # (i.e. we can finish this iteration within maxTime)
                # then we continue searching until we finish this iteration.
                # However, estimate a bit more conservatively to avoid wasting time.
                if useTimeMan:
                    if not extraTimeIter and OPTTIME and not MAXTIME:
                        move_i = rootMoves.index(move) + 1
                        if (rootMovesSize - move_i) * default_nodes * 1.2 < maxTime / 1000 * Nps():
                            if option("debug"):
                                printf(f"info string Timeman: Extra time")
                                extraTimeIter = i
                
                if extraTimeIter < i:  # true as long as we did not use extra time
                    STOP_SEARCH = OPTTIME = MAXTIME = False  # reset
                    
                    # Use previous iteration's best move since this iteration isn't complete
                    bestMove = prevBestMove
                    bestValue = prevBestValue
                    
                    try:
                        bestPv = rootMovesPv[bestMove]
                    except KeyError:
                        bestPv = [bestMove]
                    
                    time_taken = time_now() - root_time
                    printf(
                        f"info depth {i} score cp {bestValue.__uci_str__()} nodes {total_nodes} nps {int(total_nodes / time_taken)} "
                        f"time {int(time_taken * 1000)} pv {utils.pv_to_uci(bestPv)}")
                    
                    if len(bestPv) <= 1:
                        printf(f"bestmove {bestMove}")
                    else:
                        printf(f"bestmove {bestMove} ponder {bestPv[1]}")
                    IS_SEARCHING = False
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
                printf(f"info depth {i} currmove {move} currmovenumber {rootMoves.index(move) + 1} "
                       f"nodes {total_nodes}")
                last_output_time = time_now()
            
            # search
            try:
                prevEval = rootMovesEval[move]
            except KeyError:
                prevEval = None
            
            promisingValue = promising(move, rootMovesEval, rootMovesSize, i, (move == bestMove), bestValue)
            move_nodes = calc_nodes(move, bestValue, i, default_nodes, prevEval, (move == bestMove),
                                    rootMovesExtraNodes, promisingValue)
            value = Value()
            if move in rootMovesPv.keys():
                pv = rootMovesPv[move]
            else:
                pv = [move]
            
            # Pre-handling of checkmate, stalemate, draw, etc.
            IS_GAME_OVER = pos.is_game_over()
            OUTCOME = pos.outcome()
            if IS_GAME_OVER:
                if OUTCOME.winner is None:
                    value = Value(VALUE_DRAW)
                else:
                    value = Value(VALUE_MATE, OUTCOME.winner)
        
            # Before evaluating, first check if the max. move horizon has been reached
            if len(pv) >= GET_MAX_HORIZON():
                # If move horizon is reached, we give extra nodes to the move, and recalculate it later
                if not move in rootMovesExtraNodes.keys():
                    rootMovesExtraNodes[move] = 1.1
                else:
                    rootMovesExtraNodes[move] += 0.1
                continue  # skip evaluating this move currently
            
            info: chess.engine.InfoDict = __engine__(pos=pos, nodes=move_nodes)
            
            new_pv = None
            try:
                total_nodes += info["nodes"]
                new_pv = info["pv"]
                new_pv = new_pv[:MAX_MOVES]
                pv.extend(new_pv)
            except KeyError:
                pass
            
            # Update PV
            rootMovesPv[move] = pv
            
            depth = info["depth"]
            if depth not in rootMovesDepth.keys():
                rootMovesDepth[move] = depth
            
            if not IS_GAME_OVER:
                value = Value(info["score"], pos.turn)
            
            # Convert value to our pov
            value = value.to_pov(rootStm)
            
            # update rootMovesEval
            rootMovesEval[move] = value
            
            if option("debug"):
                printf(f"info string Iteration {i} | Move: {move} | Eval: {value} | POV: {value.to_pov(rootStm)}")
            
            if new_pv:
                rootMovesPos[move] = utils.push_pv(pos, new_pv, info)
            
            if value > bestValue:
                if move != bestMove:
                    bestMoveChanges += 1
                bestValue = value
                bestMove = move
        
        # proper UCI formatting
        time_taken = time_now() - root_time
        try:
            if info["nps"]:
                npsAverage.add(info["nps"])
        except Exception:
            pass
        
        printf(
            f"info depth {i} seldepth {depth} score cp {bestValue.__uci_str__()} nodes {total_nodes} nps {Nps()} "
            f"time {int(time_taken * 1000)} pv {utils.pv_to_uci(rootMovesPv[bestMove])}")
        
        prevBestValue = bestValue
        prevBestMove = bestMove
        
        # Update pruned moves after we finish searching all root moves
        for move in rootMovesEval.keys():
            v = rootMovesEval[move]
            min_prune_eval = prune_margin(bestValue, i)
            if v < min_prune_eval:
                pruned_rootMoves[move] = i
                if option("debug"):
                    printf(f"info string Iteration {i} | Pruned: {move} | Prune margin: {min_prune_eval}")
        
        # Update moves list size
        rootMovesSize = [1 for m in rootMoves if m not in pruned_rootMoves.keys()].__len__()
        
        if rootMovesSize / len(rootMoves) < 0.2:
            # Extreme case: only few moves remains after pruning
            
            # Give extra nodes to the best move
            if bestMove not in rootMovesExtraNodes.keys():
                rootMovesExtraNodes[bestMove] = 1.2  # initial bonus multiplier
            else:
                rootMovesExtraNodes[bestMove] += 0.1
        
        # Allow re-calculation of move PVs
        if ( (rootMovesSize <= 1 and i - prevRecalcIter >= recalcCount - 1) or
             rootMovesSize / len(rootMoves) <= max(0.02, 0.2 - recalcCount * 0.02) or
             bestValue - prevBestValue <= -(25 + i / 2) or (i <= 10 and bestValue - rootScore <= -(50 + i)) ) \
            and i - prevRecalcIter >= 5 + 2 * recalcCount:
            # Every move needs to be re-calculated
            nextIterRecalcMoves = rootMoves.copy()
        
        if len(nextIterRecalcMoves) > 0:
            for m in nextIterRecalcMoves:
                # Delete the end of the PV, depending on how promising the move is.
                # The more promising it is, the more we delete to allow more accurate calculation.
                p = promising(m, rootMovesEval, rootMovesSize, i, (m == bestMove),
                              bestValue)  # float from 0 to 1
                p = min(p, 0.85)
                
                # Extra bonus if PV is long
                p += len(rootMovesPv[m]) / 200
                # allow deletion of the entire PV only if i <= 30
                # p = 0 -> delete nothing, p = 1 -> delete entire PV
                max_p = 0.9 - 0.005 * i + 0.2 * math.log10(i / 30) if i > 30 else 0.8 + 0.0066 * i
                p = min(max_p, 1.0)
                
                # delete PV
                del_moves = round(len(rootMovesPv[m]) * (1 - p))
                del_moves = max(del_moves, 1 + i // 20)  # cannot delete root move
                if option("debug"):
                    printf(f"info string Iteration {i} | Kept {del_moves} moves in {m}")
                rootMovesPv[m] = rootMovesPv[m][:del_moves]
                
                # update position
                rootMovesPos[m] = utils.push_pv(rootPos.copy(), rootMovesPv[m])
            
            # Restart the search, with increased default_nodes
            default_nodes += int(Nps() * 0.10)
            rootMovesSize = len(list(rootMoves))
            pruned_rootMoves = {}
            bestValue = Value(-VALUE_INFINITE, rootStm)
            prevRecalcIter = i
            recalcCount += 1
            nextIterRecalcMoves = []
        
        # end of this iteration
        i += 1
    
    # After search is finished
    bestPv = rootMovesPv[bestMove]
    if len(bestPv) <= 1:
        printf(f"bestmove {bestMove}")
    else:
        printf(f"bestmove {bestMove} ponder {bestPv[1]}")
    
    IS_SEARCHING = False


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
               , is_best: bool, rootMovesExtraNodes: dict, promisingValue):
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
        scale *= 1.5
        
    # based on score difference
    if prevEval is not None:
        scoreDiff = max(bestValue - prevEval, 0)
        scale *= clamp(1.5 - (scoreDiff / 125.0), 0.8, 1.4)
    
    # promising
    promisingScale = max(2.0 * math.log10( max(10 * promisingValue - 2, 1.0) ),
                         min(0.2 + i * 0.005, 0.75))
    scale *= promisingScale
    
    if move in rootMovesExtraNodes.keys():
        scale *= rootMovesExtraNodes[move]
    
    scale = clamp(scale, 0.01, 10.0)  # cap min and max scale just in case
    return int(default_nodes * scale)


def setNodes(v, i: int):
    """Set default_nodes based on UCI input.
    This value is either an integer or 'auto'."""
    if type(v) == int:
        return v
    else:
        assert v == 'auto'
        scale = (1000 - option("Nodes scale")) / (75.0 + 0.5 * i)
        div = scale - math.log10(option("Threads")) - 2.0 * math.log10(i)
        div = clamp(div, 0.10, 10.0)
        return int(Nps() / div)


def promising(move: chess.Move, rootMovesEval: dict, rootMovesSize: int, i: int, is_best: bool,
              bestValue: Value):
    """
    Return a float from 0 to 1, indicating how promising a move is.
    """
    
    # If best move, return 1
    if is_best:
        return 1.0
    
    # Scale according to how much worse than bestValue eval is
    try:
        ev = rootMovesEval[move]
    except KeyError:
        ev = bestValue  # implicitly eval_score = 1.0
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


def engine_is_alive():
    try:
        engine_engine.engine.ping()
        return True
    except Exception:
        return False


def Nps():
    nps = int(npsAverage.value())
    return nps

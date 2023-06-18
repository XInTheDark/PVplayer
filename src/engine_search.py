import chess, chess.engine

import engine
import utils
from search_h import *
import query_tb
from engine_ucioption import *


def search(rootPos: chess.Board, MAX_MOVES=5, MAX_ITERS=1, depth: int = None, nodes: int = None, time: int = None,
            mate: int = None):
    """
    Search a position by tracing the PV.
    """
    
    # if no parameters are given, default to nodes
    if not depth and not nodes and not time and not mate:
        nodes = option("Nodes")
    
    i = 1
    
    rootMoves = list(rootPos.legal_moves)
    
    # first evaluation for rootPos
    info: chess.engine.InfoDict = engine.__engine__(fen=rootPos.fen(), depth=depth, nodes=nodes, time=time,
                                                    mate=mate)
    
    rootScore = info["score"].white()  # white, cp
    rootStm = rootPos.turn
    
    
    # initialise dictionary for current position after each root move
    # key: root move, value: position
    rootMovesPos = {}
    rootMovesDepth = {}
    rootMovesEval = {}
    rootMovesPv = {}
    pruned_rootMoves = {}
    rootMovesExtraNodes = {}
    
    rootMovesSize = len(list(rootMoves))
    
    bestValue = Value(-99999, rootStm)
    bestMove = None
    
    while i <= MAX_ITERS:
        currentIterTotalNodes = 0
        
        for move in rootMoves:
            if move in pruned_rootMoves.keys():
                pruned_iter = pruned_rootMoves[move]
                if pruned_iter >= 5 or pruned_iter >= i + 5:
                    # if it is pruned late, then we can assume that it is a bad move
                    continue
                else:
                    if pruned_iter - i >= 2:
                        pruned_rootMoves.pop(move)
            
            # find position in rootMovesPos: almost like a transposition table, but not quite.
            # if move is found, then we can continue searching from where we left off.
            if move in rootMovesPos.keys():
                pos = rootMovesPos[move]
            else:
                pos = rootPos.copy()
                pos.push(move)
                rootMovesPos[move] = pos
            
            # search
            
            try:
                prevEval = rootMovesEval[move]
            except KeyError:
                prevEval = None
                
            move_nodes = calc_nodes(move, bestValue, i, nodes, prevEval, (move==bestMove), rootMovesExtraNodes)
            
            info: chess.engine.InfoDict = engine.__engine__(fen=pos.fen(), depth=depth, nodes=move_nodes, time=time,
                                                            mate=mate)
            currentIterTotalNodes += info["nodes"]
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
            
            if option("UCI_DebugMode"):
                print(f"info string Iteration {i} | Move: {move} | Eval: {value}")
            
            rootMovesPos[move] = pos = utils.push_pv(pos, pv, info)
            
            if value > bestValue:
                bestValue = value
                bestMove = move
                
        # print(f"Iteration {i} | Best move: {bestMove} | Eval: {bestValue} | Depth: {depth}")
        
        # proper UCI formatting
        print(f"info depth {i} score {bestValue} nodes {currentIterTotalNodes} "
              f"pv {utils.pv_to_uci(rootMovesPv[bestMove])}")
        
        # Update pruned moves after we finish searching all root moves
        for move in rootMovesEval.keys():
            v = rootMovesEval[move]
            min_prune_eval = prune_margin(bestValue, i)
            if v < min_prune_eval:
                pruned_rootMoves[move] = i
                if option("UCI_DebugMode"):
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
            bestValue = Value(-99999, rootStm)
            bestMove = None
            
        i += 1
        
        
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
    scale = 1.0
    
    # If best move, search 30% more nodes
    if is_best or (prevEval and prevEval >= bestValue):
        scale = 1.3
    
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
    
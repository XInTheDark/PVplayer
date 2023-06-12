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
    
    rootMovesSize = len(list(rootMoves))
    
    bestValue = Value(-99999, rootStm)
    bestMove = None
    
    while i <= MAX_ITERS:
        for move in rootMoves:
            if move in pruned_rootMoves.keys():
                pruned_iter = pruned_rootMoves[move]
                if pruned_iter >= 5 or pruned_iter >= i + 5:
                    # when a move is pruned early, we can try exploring it again
                    # if it is pruned late, then we can assume that it is a bad move
                    continue
                else:
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
            # Important TODO: allow re-calculation of best move PV once best move is very promising.
            
            info: chess.engine.InfoDict = engine.__engine__(fen=pos.fen(), depth=depth, nodes=nodes, time=time,
                                                            mate=mate)
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
        print(f"info depth {i} score {bestValue} pv {utils.pv_to_uci(rootMovesPv[bestMove])}")
        
        # Update pruned moves after we finish searching all root moves
        for move in rootMovesEval.keys():
            v = rootMovesEval[move]
            if v < prune_margin(bestValue, i):
                pruned_rootMoves[move] = i
                
        # Update moves list size
        rootMovesSize = [1 for m in rootMoves if m not in pruned_rootMoves.keys()].__len__()
        
        if rootMovesSize <= 1:
            # Extreme case
            rootMovesSize = len(list(rootMoves))
            pruned_rootMoves = {}
            
        i += 1
        
        
def prune_margin(bestValue: Value, i: int):
    """
    Prune the root moves that return an eval below the margin.
    """
    
    bestValue = int(bestValue)
    
    m = bestValue - 50
    # Be more lenient with the margin for the first few iterations
    m += (3 - i) * (20 if i < 3 else 10)
    
    # Scale on bestValue: if the absolute value is large we can be more lenient
    m += (abs(bestValue) / 100) * 10 if abs(bestValue) >= 50 else 0
    
    m = int(m)
    
    return max(m, bestValue - 10)


def calc_nodes(bestValue: Value, i: int, default_nodes: int, rootMovesSize: int, prevEval, is_best):
    """
    Calculate the number of nodes to search, based on search heuristics.
    """
    
    bestValue = int(bestValue)
    
    # If best move, search 50% more nodes
    if is_best or prevEval >= bestValue:
        return int(1.5 * default_nodes)
    
    # if prevEval is close to bestValue then search some more nodes depending on rootMovesSize
    if prevEval >= bestValue - 20:
        scale = min(1.05, 1 + ((40 - rootMovesSize) / 100))
    
    
    
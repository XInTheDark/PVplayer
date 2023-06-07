import chess

def push_pv(start, pv):
    board = None
    if type(start) == str:
        board = chess.Board(start)
    elif type(start) == chess.Board:
        board = start
    
    if type(pv) == str:
        pv = pv.split('pv')[-1]
        pv = pv.split()
        
        for move in pv:
            move = chess.Move.from_uci(move)
    
    rule50 = board.halfmove_clock
    for move in pv:
        board.push(move)
        rule50 += 1
        
        # Reset rule50 count because the library implementation is somewhat broken
        if board.is_capture(move):
            rule50 = board._halfmove_clock = 0
        elif board.piece_at(move.from_square).piece_type == chess.PAWN:
            rule50 = board._halfmove_clock = 0
        
    # Correct the rule50 count in FEN
    f = board.fen().split()
    f[-2] = str(rule50)
    f = ' '.join(f)
    
    return chess.Board(f)
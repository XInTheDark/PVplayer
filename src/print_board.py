import chess

def printBoard(fen: str):
    board = chess.Board(fen)
    print(board)
    
    
if __name__ == "__main__":
    fen = input("FEN > ")
    
    printBoard(fen)
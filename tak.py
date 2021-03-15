
from enum import Enum, auto

class PieceType(Enum):
    FLAT = auto()
    WALL = auto()
    CAPSTONE = auto()

class Player(Enum):
    BLACK = -1
    WHITE = 1

class Piece:
    def __init__(self, color: Player, piece_type: PieceType):
        self.color = color
        self.piece_type = piece_type

# State.board[row][col]
# O-----col----->
# |
# |
# row
# |
# |
# v

class State:
    def __init__(self):
        self.first_turn = True
        self.current_player = Player.WHITE
        
        self.board = []
        for _ in range(5):
            l = []
            for _ in range(5):
                l.append([])
            self.board.append(l)

        self.num_flats = {
            Player.BLACK: 21,
            Player.WHITE: 21
        }
        self.num_caps = {
            Player.BLACK: 1,
            Player.WHITE: 1
        }
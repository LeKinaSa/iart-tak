
from typing import List
from enum import Enum, auto
from copy import deepcopy
from pprint import pprint


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
    
    def evaluate(self, player: Player) -> int: # TODO
        return 0
    
    def possible_moves(self) -> List:
        moves = []

        for row in range(5):
            for col in range(5):
                move_types = [PlaceFlat(row, col), PlaceWall(row, col), PlaceCap(row, col)]

                for move in move_types:
                    if move.is_valid(self):
                        moves.append(move)

        return moves
    
    def possible_states(self) -> List:
        pass
    
    def play_move(self, move): # -> State
        pass



# Pseudo-abstract class
class Move:
    def is_valid(self, state: State) -> bool:
        raise NotImplementedError()

    def play(self, state: State) -> State:
        raise NotImplementedError()

class PlaceFlat(Move):
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return len(state.board[self.row][self.col]) == 0 and state.num_flats[state.current_player] > 0
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        if state_copy.first_turn:
            state_copy.board[self.row][self.col].append(Piece(-state_copy.current_player, PieceType.FLAT))
            state_copy.num_flats[-state_copy.current_player] -= 1

            if state_copy.current_player == Player.BLACK:
                state_copy.first_turn = False
        else:
            state_copy.board[self.row][self.col].append(Piece(state_copy.current_player, PieceType.FLAT))
            state_copy.num_flats[state_copy.current_player] -= 1
        
        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return 'PlaceFlat(' + str(self.row) + ', ' + str(self.col) + ')'

class PlaceWall(Move):
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return len(state.board[self.row][self.col]) == 0 and state.num_flats[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.row][self.col].append(Piece(state_copy.current_player, PieceType.WALL))
        state_copy.num_flats[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy

class PlaceCap(Move):
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return len(state.board[self.row][self.col]) == 0 and state.num_caps[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.row][self.col].append(Piece(state_copy.current_player, PieceType.CAPSTONE))
        state_copy.num_caps[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy


state = State()
pprint(state.possible_moves())
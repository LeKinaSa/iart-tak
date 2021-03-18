
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
    def __init__(self, color: Player, type: PieceType):
        self.color = color
        self.type = type
    
    def __repr__(self):
        colors = { -1: 'w', 1: 'b' }
        types = { PieceType.FLAT: 'f', PieceType.WALL: 'w', PieceType.CAPSTONE: 'c' }

        return colors[self.color] + types[self.type]

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
        self.current_player = 1
        
        self.board = []
        for _ in range(5):
            l = []
            for _ in range(5):
                l.append([])
            self.board.append(l)

        self.num_flats = {
            1: 21,
            -1: 21
        }
        self.num_caps = {
            1: 1,
            -1: 1
        }
    
    def evaluate(self, player: Player) -> int: # TODO
        return 0
    
    def possible_moves(self) -> List:
        moves = []

        for row in range(5):
            for col in range(5):
                move_types = [PlaceFlat(row, col), PlaceWall(row, col), PlaceCap(row, col)]

                for direction in directions.values():
                    move_types.append(MovePiece(row, col, direction))

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
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return not state.board[self.row][self.col] and state.num_flats[state.current_player] > 0
    
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
        return 'PlaceFlat (' + str(self.row) + ', ' + str(self.col) + ')'

class PlaceWall(Move):
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return not state.board[self.row][self.col] and state.num_flats[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.row][self.col].append(Piece(state_copy.current_player, PieceType.WALL))
        state_copy.num_flats[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy

class PlaceCap(Move):
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self, state: State) -> bool:
        return not state.board[self.row][self.col] and state.num_caps[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.row][self.col].append(Piece(state_copy.current_player, PieceType.CAPSTONE))
        state_copy.num_caps[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy

directions = {
    'UP': [-1, 0],
    'DOWN': [1, 0],
    'LEFT': [0, -1],
    'RIGHT': [0, 1]
}

class MovePiece(Move):
    def __init__(self, row: int, col: int, direction):
        self.row = row
        self.col = col
        self.direction = direction
        self.row_to = row + direction[0]
        self.col_to = col + direction[1]
    
    def is_valid(self, state: State) -> bool:
        if self.row_to < 0 or self.row_to > 4 or self.col_to < 0 or self.col_to > 4:
            return False
        
        stack = state.board[self.row][self.col]
        if len(stack) != 1:
            return False

        piece = stack[-1]
        if piece.color != state.current_player:
            return False

        stack_to = state.board[self.row_to][self.col_to]
        if stack_to:
            piece_to = stack_to[-1]
        
            if piece_to.type == PieceType.CAPSTONE:
                return False
            
            if piece_to.type == PieceType.WALL and piece.type != PieceType.CAPSTONE:
                return False

        return True
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        stack = state_copy.board[self.row][self.col]
        piece = stack[-1]
        stack_to = state_copy.board[self.row_to][self.col_to]

        if piece.type == PieceType.CAPSTONE and stack_to and stack_to[-1].type == PieceType.WALL:
            stack_to[-1].type = PieceType.FLAT
        
        stack_to.append(piece)
        stack.pop()

        return state_copy
    
    def __repr__(self):
        return "MovePiece (" + str(self.row) + ", " + str(self.col) + ") -> (" + str(self.row_to) + ", " + str(self.col_to) + ")"

state = State()
pprint(state.possible_moves())
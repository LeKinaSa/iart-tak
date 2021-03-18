
from typing import List
from enum import Enum, auto
from copy import deepcopy
from pprint import pprint

from utils import Position

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

class Result(Enum):
    NOT_FINISHED = auto()
    BLACK_WIN = auto()
    DRAW = auto()
    WHITE_WIN = auto()

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
    
    def objective(self) -> Result:
        '''Checks if the game is finished, returning the game's result (WHITE_WIN, DRAW or BLACK_WIN) or NOT_FINISHED otherwise.'''

        def part_of_road(pos: Position, player: Player) -> bool:
            return self.board[pos.row][pos.col] and self.board[pos.row][pos.col][-1].color == player and self.board[pos.row][pos.col][-1].type != PieceType.WALL

        # Depth first search (to search for road)
        def dfs(stack: List[Position], player: Player):
            visited = set()

            while stack:
                pos = stack.pop()
                if pos not in visited:
                    visited.add(pos)
                    adjacent = [pos.up(), pos.down(), pos.left(), pos.right()]
                    
                    for adj_pos in adjacent:
                        if pos not in visited and pos.is_within_bounds() and part_of_road(pos, player):
                            stack.append(adj_pos)
            
            return visited
        
        end_rows = set(Position(row, 4) for row in range(5))
        end_cols = set(Position(4, col) for col in range(5))
        
        # Search for white road (horizontal or vertical)
        start_rows = [Position(row, 0) for row in range(5) if part_of_road(Position(row, 0), Player.WHITE)]
        start_cols = [Position(0, col) for col in range(5) if part_of_road(Position(0, col), Player.WHITE)]
        
        if end_rows.intersection(dfs(start_rows, Player.WHITE)) or end_cols.intersection(dfs(start_cols, Player.WHITE)):
            return Result.WHITE_WIN

        # Search for black road (horizontal or vertical)
        start_rows = [Position(row, 0) for row in range(5) if part_of_road(Position(row, 0), Player.BLACK)]
        start_cols = [Position(0, col) for col in range(5) if part_of_road(Position(0, col), Player.BLACK)]

        if end_rows.intersection(dfs(start_rows, Player.BLACK)) or end_cols.intersection(dfs(start_cols, Player.BLACK)):
            return Result.BLACK_WIN

        # Test for flat win
        controlled_flats = { Player.BLACK: 0, Player.WHITE: 0 }
        board_full = True
        for row in range(5):
            for col in range(5):
                if not self.board[row][col]:
                    board_full = False
                    break
                
                top = self.board[row][col][-1]
                if top.type == PieceType.FLAT:
                    controlled_flats[top.color] += 1
            
            if not board_full:
                break
        else:
            if controlled_flats[Player.WHITE] > controlled_flats[Player.BLACK]:
                return Result.WHITE_WIN
            elif controlled_flats[Player.BLACK] > controlled_flats[Player.WHITE]:
                return Result.BLACK_WIN
            return Result.DRAW

        return Result.NOT_FINISHED

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
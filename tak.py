
from typing import List
from enum import Enum, auto
from copy import deepcopy
from pprint import pprint

from utils import Position, get_partitions_with_leading_zero

class PieceType(Enum):
    FLAT = auto()
    WALL = auto()
    CAPSTONE = auto()

class Player:
    BLACK = -1
    WHITE = 1

class Piece:
    def __init__(self, color: Player, type: PieceType):
        self.color = color
        self.type = type
    
    def __repr__(self):
        colors = { Player.WHITE: 'w', Player.BLACK: 'b' }
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

# Number of pieces for each board size
flats_for_size = {
    3: 10, 4: 15, 5: 21,
    6: 30, 7: 40, 8: 50
}

capstones_for_size = {
    3: 0, 4: 0, 5: 1,
    6: 1, 7: 1, 8: 2
}

class State:
    def __init__(self, board_size = 5):
        self.first_turn = True
        self.current_player = Player.WHITE
        self.board = [[[] for _ in range(board_size)] for _ in range(board_size)]
        self.board_size = board_size

        self.num_flats = {
            Player.WHITE: flats_for_size[board_size],
            Player.BLACK: flats_for_size[board_size]
        }
        self.num_caps = {
            Player.WHITE: capstones_for_size[board_size],
            Player.BLACK: capstones_for_size[board_size]
        }
    
    def evaluate(self, player: Player) -> int: # TODO
        result = self.objective()

        if result == Result.DRAW:
            return 0
        elif (result == Result.WHITE_WIN and player == Player.WHITE) or (result == Result.BLACK_WIN and player == Player.BLACK):
            return int(1e9)
        elif (result == Result.WHITE_WIN and player == Player.BLACK) or (result == Result.BLACK_WIN and player == Player.BLACK):
            return int(-1e9)

        return 0
    
    def possible_moves(self) -> List:
        moves = []

        for row in range(self.board_size):
            for col in range(self.board_size):
                move_types = [PlaceFlat(Position(row, col)), PlaceWall(Position(row, col)), PlaceCap(Position(row, col))]

                for direction in directions.values():
                    move_types.append(MovePiece(Position(row, col), direction))

                    stack_size = len(self.board[row][col])
                    if stack_size > 1:
                        for partition in get_partitions_with_leading_zero(stack_size):
                            move_types.append(SplitStack(Position(row, col), direction, partition))

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
                        if pos not in visited and pos.is_within_bounds(0, self.board_size - 1) and part_of_road(pos, player):
                            stack.append(adj_pos)
            
            return visited
        
        end_rows = set(Position(row, 4) for row in range(self.board_size))
        end_cols = set(Position(4, col) for col in range(self.board_size))
        
        # Search for white road (horizontal or vertical)
        start_rows = [Position(row, 0) for row in range(self.board_size) if part_of_road(Position(row, 0), Player.WHITE)]
        start_cols = [Position(0, col) for col in range(self.board_size) if part_of_road(Position(0, col), Player.WHITE)]
        
        if end_rows.intersection(dfs(start_rows, Player.WHITE)) or end_cols.intersection(dfs(start_cols, Player.WHITE)):
            return Result.WHITE_WIN

        # Search for black road (horizontal or vertical)
        start_rows = [Position(row, 0) for row in range(self.board_size) if part_of_road(Position(row, 0), Player.BLACK)]
        start_cols = [Position(0, col) for col in range(self.board_size) if part_of_road(Position(0, col), Player.BLACK)]

        if end_rows.intersection(dfs(start_rows, Player.BLACK)) or end_cols.intersection(dfs(start_cols, Player.BLACK)):
            return Result.BLACK_WIN

        # Test for flat win
        controlled_flats = { Player.BLACK: 0, Player.WHITE: 0 }
        board_full = True
        for row in range(self.board_size):
            for col in range(self.board_size):
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
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_flats[state.current_player] > 0
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        if state_copy.first_turn:
            state_copy.board[self.pos.row][self.pos.col].append(Piece(-state_copy.current_player, PieceType.FLAT))
            state_copy.num_flats[-state_copy.current_player] -= 1

            if state_copy.current_player == Player.BLACK:
                state_copy.first_turn = False
        else:
            state_copy.board[self.pos.row][self.pos.col].append(Piece(state_copy.current_player, PieceType.FLAT))
            state_copy.num_flats[state_copy.current_player] -= 1
        
        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return 'PlaceFlat ' + str(self.pos)

class PlaceWall(Move):
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_flats[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.pos.row][self.pos.col].append(Piece(state_copy.current_player, PieceType.WALL))
        state_copy.num_flats[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return 'PlaceWall ' + str(self.pos)


class PlaceCap(Move):
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_caps[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        state_copy.board[self.pos.row][self.pos.col].append(Piece(state_copy.current_player, PieceType.CAPSTONE))
        state_copy.num_caps[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return 'PlaceCap ' + str(self.pos)

directions = {
    'UP': Position(-1, 0),
    'DOWN': Position(1, 0),
    'LEFT': Position(0, -1),
    'RIGHT': Position(0, 1)
}

class MovePiece(Move):
    def __init__(self, pos: Position, direction: Position):
        self.pos = pos
        self.pos_to = pos + direction
    
    def is_valid(self, state: State) -> bool:
        if state.first_turn or not self.pos_to.is_within_bounds(0, state.board_size - 1):
            return False
        
        stack = state.board[self.pos.row][self.pos.col]
        if len(stack) != 1:
            return False

        piece = stack[-1]
        if piece.color != state.current_player:
            return False

        stack_to = state.board[self.pos_to.row][self.pos_to.col]
        if stack_to:
            piece_to = stack_to[-1]
        
            if piece_to.type == PieceType.CAPSTONE:
                return False
            
            if piece_to.type == PieceType.WALL and piece.type != PieceType.CAPSTONE:
                return False

        return True
    
    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        stack = state_copy.board[self.pos.row][self.pos.col]
        piece = stack[-1]
        stack_to = state_copy.board[self.pos_to.col][self.pos_to.col]

        if piece.type == PieceType.CAPSTONE and stack_to and stack_to[-1].type == PieceType.WALL:
            stack_to[-1].type = PieceType.FLAT
        
        stack_to.append(piece)
        stack.pop()

        return state_copy
    
    def __repr__(self):
        return "MovePiece " + str(self.pos) + " -> " + str(self.pos_to)

class SplitStack(Move):
    def __init__(self, pos: Position, direction, split: List[int]):
        self.pos = pos
        self.direction = direction
        self.split = split
    
    def is_valid(self, state: State) -> bool:
        stack = state.board[self.pos.row][self.pos.col]

        if len(stack) <= 1 or stack[-1].color != state.current_player or len(stack) != sum(self.split):
            return False
        
        stack_copy = deepcopy(stack)
        for i, num_pieces in enumerate(self.split):
            if i != 0:
                if num_pieces == 0:
                    return False
                
                stack_slice, stack_copy = stack_copy[:num_pieces], stack_copy[num_pieces:]

                pos_to = self.pos + self.direction.scalar_mult(i)
                if not pos_to.is_within_bounds(0, state.board_size - 1):
                    return False
                
                stack_to = state.board[pos_to.row][pos_to.col]

                if stack_to and (stack_to[-1].type == PieceType.CAPSTONE or (stack_to[-1].type == PieceType.WALL and stack_slice[0].type != PieceType.CAPSTONE)):
                    return False

        return True

    def play(self, state: State) -> State:
        state_copy = deepcopy(state)

        stack = state_copy.board[self.pos.row][self.pos.col]
        state_copy.board[self.pos.row][self.pos.col] = []

        for i, num_pieces in enumerate(self.split):
            pos_to = self.pos + self.direction.scalar_mult(i)
            stack_to = state_copy.board[pos_to.row][pos_to.col]

            stack_slice, stack = stack[:num_pieces], stack[num_pieces:]

            if stack_slice and stack_to and stack_slice[0].type == PieceType.CAPSTONE and stack_to[-1].type == PieceType.WALL:
                stack_to[-1].type = PieceType.FLAT
            
            stack_to += stack_slice

        return state_copy
    
    def __repr__(self):
        return "SplitStack " + str(self.pos) + " | " + str(self.direction) + " | " + str(self.split)

state = State()
pprint(state.possible_moves())
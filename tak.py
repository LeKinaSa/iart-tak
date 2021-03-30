
from typing import List
from enum import Enum, auto
from copy import deepcopy
from pprint import pprint
import time

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
    
    def __hash__(self):
        return hash((self.color, self.type))

    def __eq__(self, other):
        return self.color == other.color and self.type == other.type

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
    
    def __hash__(self):
        board_tuple = tuple(tuple(tuple(self.board[row][col]) for col in range(self.board_size) for row in range(self.board_size)))
        return hash((board_tuple, self.current_player))
    
    def __eq__(self, other):
        return self.board == other.board and self.current_player == other.current_player
    
    def evaluate(self, player: Player) -> int:
        '''
        Returns a number representing the value of this game state for the given player.
        '''

        result = self.objective()

        if result == Result.DRAW:
            return 0
        elif (result == Result.WHITE_WIN and player == Player.WHITE) or (result == Result.BLACK_WIN and player == Player.BLACK):
            return int(1e9)
        elif (result == Result.WHITE_WIN and player == Player.BLACK) or (result == Result.BLACK_WIN and player == Player.BLACK):
            return int(-1e9)
        
        def heuristic_num_flats() -> int:
            value = 0

            for row in range(self.board_size):
                for col in range(self.board_size):
                    stack = self.board[row][col]
                    if stack and stack[-1].type == PieceType.FLAT:
                        # Positive if stack is controlled by the player, negative otherwise
                        value += player * stack[-1].color
            
            return value
        
        def heuristic_corner_pieces() -> int:
            value = 0
            corners = [Position(0, 0), Position(0, self.board_size - 1), Position(self.board_size - 1, 0), Position(self.board_size - 1, self.board_size - 1)]

            for position in corners:
                stack = self.board[position.row][position.col]
                if stack and stack[-1].type != PieceType.WALL:
                    value += player * stack[-1].color

            return value

        def heuristic_penalty_walls() -> int:
            value = 0

            for row in range(self.board_size):
                for col in range(self.board_size):
                    stack = self.board[row][col]
                    if len(stack) == 1 and stack[0].type == PieceType.WALL:
                        adjacent = [Position(row, col) + direction for direction in directions.values()]
                        adjacent = filter(lambda x: x.is_within_bounds(0, self.board_size - 1), adjacent)

                        # Obtain adjacent stacks which are not empty
                        adjacent_stacks = [self.board[pos.row][pos.col] for pos in adjacent]
                        adjacent_stacks = filter(lambda x: x, adjacent_stacks)

                        if not adjacent_stacks:
                            value += player * stack[0].color * -5
                        else:
                            for adj_stack in adjacent_stacks:
                                if adj_stack[-1].type == PieceType.CAPSTONE and adj_stack[-1].color != player:
                                    value += player * stack[0].color * -5
            
            return value
        
        def heuristic_captured_pieces() -> int:
            '''Calculates the number of opposing pieces each player has captured'''
            value = 0

            for row in range(self.board_size):
                for col in range(self.board_size):
                    stack = self.board[row][col]

                    if len(stack) > 1:
                        top_color = stack[-1].color
                        value += self.current_player * top_color * len(list(filter(lambda x: x.color != top_color, stack)))
            
            return value

        def heuristic_nearness_to_optimal_road() -> int:
            '''Calculates the maximum number of pieces in a single row or column for each player (i. e. the nearness to an optimal road)'''
            value_player = 0
            value_opponent = 0

            for i in range(self.board_size):
                count_player = 0
                count_opponent = 0
                
                # Get maximum number of pieces along row
                for j in range(self.board_size):
                    stack = self.board[i][j]
                    if stack:
                        if stack[-1].color == self.current_player:
                            count_player += 1
                        else:
                            count_opponent += 1
                
                value_player = max(value_player, count_player)
                value_opponent = max(value_opponent, count_opponent)

                # Get maximum number of pieces along column
                for j in range(self.board_size):
                    stack = self.board[j][i]
                    if stack:
                        if stack[-1].color == self.current_player:
                            count_player += 1
                        else:
                            count_opponent += 1
                
                value_player = max(value_player, count_player)
                value_opponent = max(value_opponent, count_opponent)

            return value_player - value_opponent
        

        # The overall evaluation can be fine-tuned by adjusting each heuristic's multiplier
        value = 10 * heuristic_num_flats() + 5 * heuristic_corner_pieces() + heuristic_penalty_walls() + 5 * heuristic_captured_pieces() + \
            3 * heuristic_nearness_to_optimal_road()

        return value
    
    def possible_moves(self) -> List:
        '''Returns a list of all valid moves for this game state.'''

        moves = []

        if self.objective() == Result.NOT_FINISHED:
            positions = []

            for row in range(self.board_size):
                for col in range(self.board_size):
                    positions.append(Position(row, col))

            for position in positions:
                move_types = [PlaceFlat(position), PlaceWall(position), PlaceCap(position)]

                for direction in directions.values():
                    move_types.append(MovePiece(position, direction))

                    stack_size = len(self.board[position.row][position.col])
                    if stack_size > 1:
                        for partition in get_partitions_with_leading_zero(stack_size):
                            move_types.append(SplitStack(position, direction, partition))

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
    
    # Statistics for the negamax algorithm
    nm_calls = 0
    nm_prunings = 0
    nm_cache_hits = 0
    nm_time_possible_moves = 0
    nm_time_evaluating = 0

    transposition_cache = {}
    def negamax(self, depth: int, pruning: bool = False, caching: bool = False, statistics: bool = False):
        '''
        Implementation of the negamax algorithm, a variant of minimax that takes advantage of the
        zero-sum property of two-player adversarial games. Includes parameters for specifying the
        maximum depth, whether alpha-beta pruning is used, whether a transposition cache is used to
        avoid exploring the same positions more than once and whether statistics about the algorithm
        are printed to the console.
        '''

        if depth <= 0:
            return None
        
        alpha, beta = 0, 0
        if pruning:
            alpha, beta = int(-1e9), int(1e9)

        if caching:
            State.transposition_cache = {}

        if statistics:
            State.nm_calls = 0
            State.nm_prunings = 0
            State.nm_cache_hits = 0
            State.nm_time_possible_moves = 0
            State.nm_time_evaluating = 0

        _, move = self.negamax_recursive(depth, pruning, caching, statistics, alpha, beta, 1)

        if statistics:
            print("Number of positions analysed:", State.nm_calls)
            print("Number of cuts:", State.nm_prunings)
            print("Number of cache hits:", State.nm_cache_hits)
            print("Time spent calculting possible moves:", State.nm_time_possible_moves)
            print("Time spent evaluating:", State.nm_time_evaluating)

        return move
    
    def negamax_recursive(self, depth: int, pruning: bool, caching: bool, statistics: bool, alpha: int, beta: int, player: int):
        if statistics:
            State.nm_calls += 1
        
        if caching and self in State.transposition_cache:
            State.nm_cache_hits += 1
            return State.transposition_cache[self]

        start = time.time()
        moves = self.possible_moves()
        end = time.time()

        if statistics:
            State.nm_time_possible_moves += end - start

        # Maximum depth has been reached or no possible moves (game has ended): run evaluation function
        if depth == 0 or not moves:
            start = time.time()
            evaluation = self.evaluate(self.current_player)
            end = time.time()

            if statistics:
                State.nm_time_evaluating += end - start

            if caching:
                State.transposition_cache[self] = evaluation, None
            
            return evaluation, None

        best_move = None
        max_value = int(-1e9)

        for move in moves:
            new_state = move.play(self)
            
            value, _ = new_state.negamax_recursive(depth - 1, pruning, caching, statistics, -beta, -alpha, -player)
            value = -value

            if value > max_value:
                max_value = value
                best_move = move
            
            if pruning:
                alpha = max(alpha, max_value)
                if alpha >= beta:
                    if statistics:
                        State.nm_prunings += 1
                    break

        if caching:
            State.transposition_cache[self] = max_value, best_move
        
        return max_value, best_move
    
    def minimax(self, depth: int, pruning: bool):
        if depth <= 0:
            return None
        alpha = 0
        beta = 0
        if pruning:
            alpha = int(-1e9)
            beta  = int(1e9)
        (_, move) = self.minimax_max(depth, pruning, alpha, beta)
        return move
    
    def minimax_max(self, depth: int, pruning: bool, alpha: int, beta: int):
        moves = self.possible_moves()

        if depth == 0 or not moves:
            return self.evaluate(self.current_player), None
        
        best_move = None
        max_value = int(-1e9)
        for move in moves:
            new_state = move.play(self)
            
            value, _ = new_state.minimax_min(depth - 1, pruning, alpha, beta)
            
            if value > max_value:
                max_value = value
                best_move = move
            
            if pruning:
                if max_value >= beta:
                    return (max_value, move)
        
                if max_value > alpha:
                    alpha = max_value
            
        return max_value, best_move
    
    def minimax_min(self, depth: int, pruning: bool, alpha: int, beta: int):
        moves = self.possible_moves()
        
        if depth == 0 or not moves:
            return self.evaluate(self.current_player), None
        
        best_move = None
        min_value = int(1e9)
        for move in moves:
            new_state = move.play(self)
            
            value, _ = new_state.minimax_max(depth - 1, pruning, alpha, beta)
            
            if value < min_value:
                min_value = value
                best_move = move
            
            if pruning:
                if min_value <= alpha:
                    return (min_value, move)
    
                if min_value < beta:
                    beta = min_value
            
        return min_value, best_move
    
    def to_dict(self) -> dict:
        return {
            'board': self.board,
            'current_player': self.current_player,
            'num_flats': self.num_flats,
            'num_caps': self.num_caps
        }


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
        stack_to = state_copy.board[self.pos_to.row][self.pos_to.col]

        if piece.type == PieceType.CAPSTONE and stack_to and stack_to[-1].type == PieceType.WALL:
            stack_to[-1].type = PieceType.FLAT
        
        stack_to.append(piece)
        stack.pop()

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return "MovePiece " + str(self.pos) + " -> " + str(self.pos_to)

class SplitStack(Move):
    def __init__(self, pos: Position, direction: Position, split: List[int]):
        self.pos = pos
        self.direction = direction
        self.split = split
    
    def is_valid(self, state: State) -> bool:
        stack = state.board[self.pos.row][self.pos.col]

        if len(stack) <= 1 or len(self.split) <= 1 or stack[-1].color != state.current_player or len(stack) != sum(self.split):
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

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def __repr__(self):
        return "SplitStack " + str(self.pos) + " | " + str(self.direction) + " | " + str(self.split)

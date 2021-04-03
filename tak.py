
from typing import List, Callable
from enum import Enum, auto
import copy
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

class CachingFlag:
    EXACT = auto()
    LOWERBOUND = auto()
    UPPERBOUND = auto()

def heuristic_num_flats(state, player) -> int:
    '''Calculates the number of flats each player controls (useful for obtaining a flat win)'''
    value = 0

    for row in range(state.board_size):
        for col in range(state.board_size):
            stack = state.board[row][col]
            if stack and stack[-1].type == PieceType.FLAT:
                # Positive if stack is controlled by the player, negative otherwise
                value += player * stack[-1].color
    
    return value

def heuristic_corner_pieces(state, player) -> int:
    '''
    Adds value to controlling the corners, since they can be used to form a road both horizontally
    and vertically
    '''
    value = 0
    corners = [Position(0, 0), Position(0, state.board_size - 1), Position(state.board_size - 1, 0), Position(state.board_size - 1, state.board_size - 1)]

    for position in corners:
        stack = state.board[position.row][position.col]
        if stack and stack[-1].type != PieceType.WALL:
            value += player * stack[-1].color

    return value

def heuristic_penalty_walls(state, player) -> int:
    '''Adds a penalty for having walls near empty spaces or having walls near an opponent's capstone'''
    value = 0

    for row in range(state.board_size):
        for col in range(state.board_size):
            stack = state.board[row][col]
            if len(stack) == 1 and stack[0].type == PieceType.WALL:
                adjacent = [Position(row, col) + direction for direction in directions.values()]
                adjacent = filter(lambda x: x.is_within_bounds(0, state.board_size - 1), adjacent)

                # Obtain adjacent stacks which are not empty
                adjacent_stacks = [state.board[pos.row][pos.col] for pos in adjacent]
                adjacent_stacks = filter(lambda x: x, adjacent_stacks)

                if not adjacent_stacks:
                    value -= player * stack[0].color
                else:
                    for adj_stack in adjacent_stacks:
                        if adj_stack[-1].type == PieceType.CAPSTONE and adj_stack[-1].color != player:
                            value -= player * stack[0].color
    
    return value

def heuristic_captured_pieces(state, player) -> int:
    '''Calculates the number of opposing pieces each player has captured'''
    value = 0

    for row in range(state.board_size):
        for col in range(state.board_size):
            stack = state.board[row][col]

            if len(stack) > 1:
                top_color = stack[-1].color
                value += player * top_color * len(list(filter(lambda x: x.color != top_color, stack)))
    
    return value

def heuristic_nearness_to_optimal_road(state, player) -> int:
    '''Calculates the maximum number of pieces in a single row or column for each player (i. e. the nearness to an optimal road)'''
    value_player = 0
    value_opponent = 0

    for i in range(state.board_size):
        count_player = 0
        count_opponent = 0
        
        # Get maximum number of pieces along row
        for j in range(state.board_size):
            stack = state.board[i][j]
            if stack:
                if stack[-1].color == player:
                    count_player += 1
                else:
                    count_opponent += 1
        
        value_player = max(value_player, count_player)
        value_opponent = max(value_opponent, count_opponent)

        count_player = 0
        count_opponent = 0

        # Get maximum number of pieces along column
        for j in range(state.board_size):
            stack = state.board[j][i]
            if stack:
                if stack[-1].color == player:
                    count_player += 1
                else:
                    count_opponent += 1
        
        value_player = max(value_player, count_player)
        value_opponent = max(value_opponent, count_opponent)

    return value_player - value_opponent

def heuristic_influence(state, player) -> int:
    '''
    Calculates the number of squares a player's pieces can influence (similar to space control in Chess).
    Only considers flat pieces and does not consider stacks of height > 1, since the calculations become
    vastly more complicated when considering the splitting of stacks.
    '''
    value = 0

    for row in range(state.board_size):
        for col in range(state.board_size):
            stack = state.board[row][col]

            if len(stack) == 1 and stack[0].type == PieceType.FLAT:
                pos = Position(row, col)
                adjacent = [pos.up(), pos.down(), pos.left(), pos.right()]
                adjacent = filter(lambda pos: pos.is_within_bounds(0, state.board_size - 1), adjacent)

                protected = False
                for adj_pos in adjacent:
                    adj_stack = state.board[adj_pos.row][adj_pos.col]

                    if len(adj_stack) == 1 and adj_stack[0].type == PieceType.FLAT and adj_stack[0].color == stack[0].color:
                        protected = True
                        break
                
                for adj_pos in adjacent:
                    adj_stack = state.board[adj_pos.row][adj_pos.col]

                    if not adj_stack or (protected and len(adj_stack) == 1 and adj_stack[0].color != stack[0].color):
                        value += stack[0].color * player

    return value

def evaluate(state, player: Player, level: int = 3) -> int:
    '''Returns a number representing the value of this game state for the given player'''

    result = state.objective()

    if result == Result.DRAW:
        return 0
    elif (result == Result.WHITE_WIN and player == Player.WHITE) or (result == Result.BLACK_WIN and player == Player.BLACK):
        return int(1e9)
    elif (result == Result.WHITE_WIN and player == Player.BLACK) or (result == Result.BLACK_WIN and player == Player.WHITE):
        return int(-1e9)

    value = 0

    # The overall evaluation can be fine-tuned by adjusting each heuristic's multiplier
    if level == 1:
        value = 10 * heuristic_num_flats(state, player) + 3 * heuristic_captured_pieces(state, player) + heuristic_influence(state, player)
    elif level == 2:
        value = 10 * heuristic_num_flats(state, player) + 3 * heuristic_captured_pieces(state, player) + heuristic_influence(state, player) + heuristic_penalty_walls(state, player)
    elif level == 3:
        value = 10 * heuristic_num_flats(state, player) + heuristic_penalty_walls(state, player) + heuristic_influence(state, player) + \
            3 * heuristic_captured_pieces(state, player) + heuristic_nearness_to_optimal_road(state, player)

    return value

def evaluate_easy(state, player: Player) -> int:
    return evaluate(state, player, 1)

def evaluate_medium(state, player: Player) -> int:
    return evaluate(state, player, 2)

def evaluate_hard(state, player: Player) -> int:
    return evaluate(state, player, 3)


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
    
    def copy(self):
        state_copy = State(self.board_size)

        state_copy.first_turn = self.first_turn
        state_copy.current_player = self.current_player
        state_copy.num_flats = copy.copy(self.num_flats)
        state_copy.num_caps = copy.copy(self.num_caps)

        for row in range(self.board_size):
            for col in range(self.board_size):
                state_copy.board[row][col] = copy.copy(self.board[row][col])
        
        return state_copy
    
    def __hash__(self):
        board_tuple = tuple(tuple(tuple(self.board[row][col]) for col in range(self.board_size) for row in range(self.board_size)))
        return hash((board_tuple, self.current_player))
    
    def __eq__(self, other):
        return self.board == other.board and self.current_player == other.current_player
    
    def possible_moves(self) -> List:
        '''Returns a list of all valid moves for this game state.'''

        moves = []

        if self.objective() == Result.NOT_FINISHED:
            positions = []

            for row in range(self.board_size):
                for col in range(self.board_size):
                    positions.append(Position(row, col))

            for position in positions:
                stack_size = len(self.board[position.row][position.col])

                if stack_size == 0:
                    moves += [PlaceFlat(position), PlaceWall(position), PlaceCap(position)]
                else:
                    for direction in directions.values():
                        moves.append(MovePiece(position, direction))

                        if stack_size > 1:
                            for partition in get_partitions_with_leading_zero(stack_size):
                                moves.append(SplitStack(position, direction, partition))

        return list(filter(lambda move: move.is_valid(self), moves))
    
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
                        if adj_pos not in visited and adj_pos.is_within_bounds(0, self.board_size - 1) and part_of_road(adj_pos, player):
                            stack.append(adj_pos)
            
            return visited
        
        end_rows = set(Position(row, self.board_size - 1) for row in range(self.board_size))
        end_cols = set(Position(self.board_size - 1, col) for col in range(self.board_size))
        
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
    def negamax(self, depth: int, evaluation_function: Callable = evaluate_hard, pruning: bool = False, caching: bool = False, statistics: bool = False):
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
            alpha, beta = int(-1e10), int(1e10)

        if caching:
            State.transposition_cache = {}

        if statistics:
            State.nm_calls = 0
            State.nm_prunings = 0
            State.nm_cache_hits = 0
            State.nm_time_possible_moves = 0
            State.nm_time_evaluating = 0

        start = time.time()
        _, move = self.negamax_recursive(depth, evaluation_function, pruning, caching, statistics, alpha, beta, 1)
        end = time.time()

        if statistics:
            print("Total execution time:", end - start)
            print("Number of positions analysed:", State.nm_calls)
            print("Number of cuts:", State.nm_prunings)
            print("Number of cache hits:", State.nm_cache_hits)
            print("Time spent calculting possible moves:", State.nm_time_possible_moves)
            print("Time spent evaluating:", State.nm_time_evaluating)

        return move
    
    def negamax_recursive(self, depth: int, evaluation_function: Callable, pruning: bool, caching: bool, statistics: bool, alpha: int, beta: int, player: int):
        original_alpha = alpha
        
        if statistics:
            State.nm_calls += 1
        
        if caching and self in State.transposition_cache:
            cache_depth, flag, ret = State.transposition_cache[self]
            if cache_depth >= depth:
                State.nm_cache_hits += 1

                if flag == CachingFlag.EXACT:
                    return ret
                elif flag == CachingFlag.LOWERBOUND:
                    alpha = max(alpha, ret[0])
                elif flag == CachingFlag.UPPERBOUND:
                    beta = min(beta, ret[0])

                if alpha >= beta:
                    if statistics:
                        State.nm_prunings += 1
                    return ret

        start = time.time()
        moves = self.possible_moves()
        end = time.time()

        if statistics:
            State.nm_time_possible_moves += end - start

        # Maximum depth has been reached or no possible moves (game has ended): run evaluation function
        if depth == 0 or not moves:
            start = time.time()
            evaluation = evaluation_function(self, self.current_player)
            end = time.time()

            if statistics:
                State.nm_time_evaluating += end - start
            
            return evaluation, None

        best_move = None
        max_value = int(-1e10)

        for move in moves:
            new_state = move.play(self)
            
            value = -new_state.negamax_recursive(depth - 1, evaluation_function, pruning, caching, statistics, -beta, -alpha, -player)[0]

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
            flag = CachingFlag.EXACT
            if max_value <= original_alpha:
                flag = CachingFlag.UPPERBOUND
            elif max_value >= beta:
                flag = CachingFlag.LOWERBOUND

            State.transposition_cache[self] = depth, flag, (max_value, best_move)
        
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
            return evaluate(self, self.current_player), None
        
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
            return evaluate(self, self.current_player), None
        
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
        board_json = [[[repr(piece) for piece in stack] for stack in row] for row in self.board]

        return {
            'board': board_json,
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
    
    def to_dict(self) -> dict:
        raise NotImplementedError()

class PlaceFlat(Move):
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_flats[state.current_player] > 0
    
    def play(self, state: State) -> State:
        state_copy = state.copy()

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
    
    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'pos': [self.pos.row, self.pos.col]
        }

    def __repr__(self):
        return 'PlaceFlat ' + str(self.pos)

class PlaceWall(Move):
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_flats[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = state.copy()

        state_copy.board[self.pos.row][self.pos.col].append(Piece(state_copy.current_player, PieceType.WALL))
        state_copy.num_flats[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'pos': [self.pos.row, self.pos.col]
        }
    
    def __repr__(self):
        return 'PlaceWall ' + str(self.pos)

class PlaceCap(Move):
    def __init__(self, pos: Position):
        self.pos = pos

    def is_valid(self, state: State) -> bool:
        return not state.board[self.pos.row][self.pos.col] and state.num_caps[state.current_player] > 0 and not state.first_turn
    
    def play(self, state: State) -> State:
        state_copy = state.copy()

        state_copy.board[self.pos.row][self.pos.col].append(Piece(state_copy.current_player, PieceType.CAPSTONE))
        state_copy.num_caps[state_copy.current_player] -= 1

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'pos': [self.pos.row, self.pos.col]
        }

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
        self.direction = direction
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
        state_copy = state.copy()

        stack = state_copy.board[self.pos.row][self.pos.col]
        piece = stack[-1]
        stack_to = state_copy.board[self.pos_to.row][self.pos_to.col]

        if piece.type == PieceType.CAPSTONE and stack_to and stack_to[-1].type == PieceType.WALL:
            stack_to[-1].type = PieceType.FLAT
        
        stack_to.append(piece)
        stack.pop()

        state_copy.current_player = -state_copy.current_player
        return state_copy
    
    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'pos': [self.pos.row, self.pos.col],
            'direction': [self.direction.row, self.direction.col]
        }

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
        
        stack_copy = copy.copy(stack)
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
        state_copy = state.copy()

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
    
    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'pos': [self.pos.row, self.pos.col],
            'direction': [self.direction.row, self.direction.col],
            'split': self.split
        }

    def __repr__(self):
        return "SplitStack " + str(self.pos) + " | " + str(self.direction) + " | " + str(self.split)

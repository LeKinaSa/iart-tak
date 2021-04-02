
class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __repr__(self):
        return "(" + str(self.row) + ", " + str(self.col) + ")"
    
    def __eq__(self, other):
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))

    def __add__(self, other):
        return Position(self.row + other.row, self.col + other.col)

    def __sub__(self, other):
        return Position(self.row - other.row, self.col - other.col)
    
    def scalar_mult(self, scalar: int):
        return Position(self.row * scalar, self.col * scalar)

    def up(self):
        return Position(self.row - 1, self.col)
    
    def down(self):
        return Position(self.row + 1, self.col)

    def left(self):
        return Position(self.row, self.col - 1)

    def right(self):
        return Position(self.row, self.col + 1)
    
    def is_within_bounds(self, lower, upper) -> bool:
        return self.row >= lower and self.row <= upper and self.col >= lower and self.col <= upper


def get_partitions_with_leading_zero(num: int) -> set:
    '''
    In addition to all partitions for a given number, also returns every partition with a zero 
    added at the start. This is useful for implementing the game Tak, since it effectively
    represents splitting and moving a stack.
    '''
    partitions = get_partitions(num)
    return partitions.union(set((0, ) + partition for partition in partitions))

partition_cache = {}
def get_partitions(num: int) -> set:
    '''
    Function that calculates all possible partitions of a given number (considering all permutations).
    The function uses memoization for optimization purposes, since the amount of additional memory used
    is trivial when compared to the speedup obtained.
    '''
    if num in partition_cache:
        return partition_cache[num]

    answer = set()
    answer.add((num, ))

    for x in range(1, num):
        for y in get_partitions(num - x):
            answer.add((x, ) + y)

    partition_cache[num] = answer
    return answer


class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __repr__(self):
        return "(" + self.row + ", " + self.col + ")"
    
    def __eq__(self, other):
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))

    def up(self):
        return Position(self.row - 1, self.col)
    
    def down(self):
        return Position(self.row + 1, self.col)

    def left(self):
        return Position(self.row, self.col - 1)

    def right(self):
        return Position(self.row, self.col + 1)
    
    def is_within_bounds(self, lower = 0, upper = 4) -> bool:
        return self.row >= lower and self.row <= upper and self.col >= lower and self.col <= upper
    
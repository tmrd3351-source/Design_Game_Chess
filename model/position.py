class Position:

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def equals(self, other):
        return self.row == other.row and self.col == other.col

    def get_row(self):
        return self.row

    def get_col(self):
        return self.col

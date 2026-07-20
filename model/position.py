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

    def to_dict(self):
        return {"row": self.row, "col": self.col}

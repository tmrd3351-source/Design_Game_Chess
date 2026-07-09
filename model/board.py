class Board:

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[None] * cols for _ in range(rows)]

    def add_piece(self, piece):
        position = piece.get_position()
        self.grid[position.get_row()][position.get_col()] = piece

    def remove_piece(self, position):
        self.grid[position.get_row()][position.get_col()] = None

    def move_piece(self, source, destination):
        piece = self.get_piece(source)
        self.remove_piece(source)
        piece.set_position(destination)
        self.add_piece(piece)

    def get_piece(self, position):
        return self.grid[position.get_row()][position.get_col()]

    def is_occupied(self, position):
        return self.get_piece(position) is not None

    def inside_bounds(self, position):
        return 0 <= position.get_row() < self.rows and 0 <= position.get_col() < self.cols

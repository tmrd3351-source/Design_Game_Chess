from constants import EMPTY_CELL


class Board:

    def __init__(self, grid):
        self._grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows else 0

    def print_board(self):
        for row in self._grid:
            print(" ".join(row))

    def get_cell(self, row, col):
        return self._grid[row][col]

    def set_cell(self, row, col, value):
        self._grid[row][col] = value

    def get_row(self, row):
        return self._grid[row]

    def move_piece(self, r1, c1, r2, c2):
        piece = self.get_cell(r1, c1)
        self.set_cell(r2, c2, piece)
        self.set_cell(r1, c1, EMPTY_CELL)

    def inside_board(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_path_clear(self, r1, c1, r2, c2):
        """בורקת האם המסלול שבין (r1, c1) ל-(r2, c2) פנוי (לא כולל נקודת המוצא והיעד)"""
        dr = r2 - r1
        dc = c2 - c1

        step_r = (dr // abs(dr)) if dr != 0 else 0
        step_c = (dc // abs(dc)) if dc != 0 else 0

        curr_r = r1 + step_r
        curr_c = c1 + step_c

        while (curr_r, curr_c) != (r2, c2):
            if self._grid[curr_r][curr_c] != EMPTY_CELL:
                return False
            curr_r += step_r
            curr_c += step_c

        return True
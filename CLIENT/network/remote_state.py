from SHARED.model.position import Position


class RemotePiece:
    """Read-only view over a Piece.to_dict() snapshot - exposes just enough
    of the real Piece interface for Renderer/AnimationManager to draw it."""

    def __init__(self, data):
        self.id = data["id"]
        self._color = data["color"]
        self._kind = data["kind"]
        self._position = Position(data["position"]["row"], data["position"]["col"])
        self._state = data["state"]
        self._rest_type = data["rest_type"]
        self._rest_progress = data["rest_progress"]

    def get_color(self):
        return self._color

    def get_kind(self):
        return self._kind

    def get_position(self):
        return self._position

    def get_state(self):
        return self._state

    def get_rest_type(self):
        return self._rest_type

    def get_rest_progress(self):
        return self._rest_progress


class RemoteBoard:
    """Read-only view over a Board.to_dict() snapshot."""

    def __init__(self, data):
        self.rows = data["rows"]
        self.cols = data["cols"]
        pieces = [RemotePiece(piece_data) for piece_data in data["pieces"]]
        self._pieces_by_cell = {
            (piece.get_position().get_row(), piece.get_position().get_col()): piece
            for piece in pieces
        }
        self._pieces_by_id = {piece.id: piece for piece in pieces}

    def get_piece(self, position):
        return self._pieces_by_cell.get((position.get_row(), position.get_col()))

    def find_piece_by_id(self, piece_id):
        return self._pieces_by_id.get(piece_id)


class RemoteMotion:
    """Read-only view over a Motion.to_dict() snapshot. `piece` is the
    matching RemotePiece from the same snapshot's RemoteBoard, so identity
    comparisons (like Renderer's "is this piece mid-motion") work the same
    way they do for the real Motion/Piece."""

    def __init__(self, data, piece):
        self.piece = piece
        self.kind = data["kind"]
        self.sequence = data["sequence"]
        self.progress = data["progress"]
        self.origin = Position(data["origin"]["row"], data["origin"]["col"])
        self.source = Position(data["source"]["row"], data["source"]["col"])
        self.destination = Position(data["destination"]["row"], data["destination"]["col"])


class RemoteGameState:
    """Read-only view over a GameState.to_dict() snapshot - exposes the same
    shape as the real GameState so GuiRenderer can draw it unmodified."""

    def __init__(self, data):
        self.board = RemoteBoard(data["board"])
        self.winner = data["winner"]
        self.game_over = data["game_over"]
        self.motions = [
            RemoteMotion(motion_data, self.board.find_piece_by_id(motion_data["piece_id"]))
            for motion_data in data["motions"]
        ]
        self.move_log = [
            {
                "color": entry["color"],
                "kind": entry["kind"],
                "source": Position(entry["source"]["row"], entry["source"]["col"]),
                "destination": Position(entry["destination"]["row"], entry["destination"]["col"]),
                "captured": entry["captured"],
            }
            for entry in data.get("move_log", [])
        ]
        self.score = data.get("score", {"w": 0, "b": 0})

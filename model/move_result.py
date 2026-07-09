class MoveResult:

    def __init__(self, is_valid, reason):
        self.is_valid = is_valid
        self.reason = reason

    @staticmethod
    def legal():
        return MoveResult(True, "legal")

    @staticmethod
    def illegal(reason):
        return MoveResult(False, reason)

from SERVER.setup.parser import parse_input, validate, build_board


class GameSetup:
    """Reads and validates the input stream, producing a ready-to-use board and commands."""

    def load(self):
        tokens, commands = parse_input()
        error = validate(tokens)

        if error:
            print(error)
            return None

        return build_board(tokens), commands

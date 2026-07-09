<<<<<<< HEAD
from app import Application

Application().run()
=======
# Repository URL: not configured in this workspace
# If a git remote origin exists, replace this comment with the repository URL.

from parser import parse_input
from validator import validate
from game import Game

board, commands = parse_input()
error = validate(board)

if error:
    print(error)
else:
    game = Game(board)
    for command in commands:
        game.apply_command(command)
>>>>>>> b82f4e66ecff5eda3009f2e917cfaea4a891690e

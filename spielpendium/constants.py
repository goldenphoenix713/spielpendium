import os
import pathlib

IMAGE_SIZE = 256

ROOT_DIR = pathlib.Path(__file__).parents[1].absolute()

PROGRAM_NAME = ROOT_DIR.name

LOG_FILE = f'{ROOT_DIR}{os.sep}log{os.sep}{PROGRAM_NAME}.log'
DB_FILE = f'{ROOT_DIR}{os.sep}db{os.sep}{PROGRAM_NAME}.sqlite'

from enum import Enum
import string
from string import ascii_letters, ascii_lowercase, ascii_uppercase

from common import ascii_characters




class Mode(Enum):
    # Building the main vertical list.
    vertical_mode = 'V'
    # Building a vertical list for a vbox.
    internal_vertical_mode = 'IV'
    # Building a horizontal list for a paragraph.
    horizontal_mode = 'H'
    # Building a horizontal list for an hbox.
    restricted_horizontal_mode = 'RH'
    # Building a formula to be placed in a horizontal list.
    math_mode = 'M'
    # Building a formula to be placed on a line by itself,
    # interrupting the current paragraph.
    display_math_mode = 'DM'


class Interpreter(object):

    def __init__(self):
        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.mode = Mode.vertical_mode


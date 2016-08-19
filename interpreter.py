from collections import namedtuple
from enum import Enum
import string
from string import ascii_letters, ascii_lowercase, ascii_uppercase

from common import ascii_characters


math_classes = [
    'ordinary',  # 0
    'large_operator',  # 1
    'binary_relation',  # 2
    'relation',  # 3
    'opening',  # 4
    'closing',  # 5
    'punctuation',  # 6
    'variable_family',  # 7
    'special_active',  # 8 (weird special case)
]

MathClass = Enum('MathClass', {symbol: i for i, symbol in enumerate(math_classes)})

GlyphCode = namedtuple('GlyphCode', ('family', 'position'))
ignored_glyph_code = GlyphCode(family=0, position=0)

MathCode = namedtuple('MathCode', ('math_class', 'glyph_code'))
active_math_code = MathCode(math_class=MathClass.special_active,
                            glyph_code=ignored_glyph_code)

DelimiterCode = namedtuple('DelimiterCode',
                           ('small_glyph_code', 'large_glyph_code'))
not_a_delimiter_code = DelimiterCode(small_glyph_code=None,
                                     large_glyph_code=None)
ignored_delimiter_code = DelimiterCode(
    small_glyph_code=ignored_glyph_code,
    large_glyph_code=ignored_glyph_code
)


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
        self.initialize_char_math_codes()
        self.initialize_case_codes()
        self.initialize_space_factor_codes()
        self.initialize_delimiter_codes()

    def initialize_char_math_codes(self):
        self.char_to_math_code = {}
        for i, c in enumerate(ascii_characters):
            if c in ascii_letters:
                family = 1
            else:
                family = 0
            if c in (ascii_letters + string.digits):
                math_class = MathClass.variable_family
            else:
                math_class = MathClass.ordinary
            glyph_code = GlyphCode(family=family, position=i)
            self.char_to_math_code[i] = MathCode(math_class, glyph_code)
            # TODO: handle special active_math_code value,
            # page 155 of The TeXbook.

    def initialize_case_codes(self):
        self.lower_case_code, self.upper_case_code = [
            {c: chr(0) for c in ascii_characters}
            for _ in range(2)
        ]
        for lower, upper in zip(ascii_lowercase, ascii_uppercase):
            self.lower_case_code[lower] = lower
            self.upper_case_code[upper] = upper
            self.lower_case_code[upper] = lower
            self.upper_case_code[lower] = upper

    def initialize_space_factor_codes(self):
        self.space_factor_code = {c: (999 if c in ascii_uppercase else 1000)
                                  for c in ascii_characters}

    def initialize_delimiter_codes(self):
        self.delimiter_code = {c: not_a_delimiter_code
                               for c in ascii_characters}
        self.delimiter_code['.'] = ignored_delimiter_code

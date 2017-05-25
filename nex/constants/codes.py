"""
Define structure and values of TeX's internal 'codes', which map characters
to values such as their category (letter, space, comment and such),
how they behave in mathematics (binary relation, large operator and such),
and their status as delimiters.
"""
from collections import namedtuple
from enum import Enum


class CatCode(Enum):
    escape = 0
    begin_group = 1
    end_group = 2
    math_shift = 3
    align_tab = 4
    end_of_line = 5
    parameter = 6
    superscript = 7
    subscript = 8
    ignored = 9
    space = 10
    letter = 11
    other = 12
    active = 13
    comment = 14
    invalid = 15


class WeirdChar(Enum):
    null = chr(0)
    line_feed = chr(10)
    carriage_return = chr(13)
    delete = chr(127)


class MathClass(Enum):
    ordinary = 0
    large_operator = 1
    binary_relation = 2
    relation = 3
    opening = 4
    closing = 5
    punctuation = 6
    variable_family = 7
    special_active = 8  # Weird special case.


GlyphCode = namedtuple('GlyphCode', ('family', 'position'))
ignored_glyph_code = GlyphCode(family=0, position=0)

MathCode = namedtuple('MathCode', ('math_class', 'glyph_code'))
active_math_code = MathCode(MathClass.special_active, ignored_glyph_code)

DelimiterCode = namedtuple('DelimiterCode',
                           ('small_glyph_code', 'large_glyph_code'))
not_a_delimiter_code = DelimiterCode(small_glyph_code=None,
                                     large_glyph_code=None)
ignored_delimiter_code = DelimiterCode(small_glyph_code=ignored_glyph_code,
                                       large_glyph_code=ignored_glyph_code)

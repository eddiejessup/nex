from string import ascii_letters

from ..codes import CatCode


literals_map = {
    ('<', CatCode.other): 'LESS_THAN',
    ('>', CatCode.other): 'GREATER_THAN',

    ('=', CatCode.other): 'EQUALS',
    ('+', CatCode.other): 'PLUS_SIGN',
    ('-', CatCode.other): 'MINUS_SIGN',

    ('0', CatCode.other): 'ZERO',
    ('1', CatCode.other): 'ONE',
    ('2', CatCode.other): 'TWO',
    ('3', CatCode.other): 'THREE',
    ('4', CatCode.other): 'FOUR',
    ('5', CatCode.other): 'FIVE',
    ('6', CatCode.other): 'SIX',
    ('7', CatCode.other): 'SEVEN',
    ('8', CatCode.other): 'EIGHT',
    ('9', CatCode.other): 'NINE',

    ('\'', CatCode.other): 'SINGLE_QUOTE',
    ('"', CatCode.other): 'DOUBLE_QUOTE',
    ('`', CatCode.other): 'BACKTICK',

    ('.', CatCode.other): 'POINT',
    (',', CatCode.other): 'COMMA',
}

hex_letters_map = {
    ('A', CatCode.other): 'A',
    ('B', CatCode.other): 'B',
    ('C', CatCode.other): 'C',
    ('D', CatCode.other): 'D',
    ('E', CatCode.other): 'E',
    ('F', CatCode.other): 'F',
    ('A', CatCode.letter): 'A',
    ('B', CatCode.letter): 'B',
    ('C', CatCode.letter): 'C',
    ('D', CatCode.letter): 'D',
    ('E', CatCode.letter): 'E',
    ('F', CatCode.letter): 'F',
}
literals_map.update(hex_letters_map)

non_active_literals_map = {c: 'NON_ACTIVE_UNCASED_{}'.format(c.lower())
                           for c in ascii_letters}


other_literal_type = 'MISC_CHAR_CAT_PAIR'

# TODO: There are non-terminal tokens in here, which rply will get told *are*
# terminal tokens.
category_map = {
    CatCode.space: 'SPACE',
    CatCode.begin_group: 'LEFT_BRACE',
    CatCode.end_group: 'RIGHT_BRACE',
    CatCode.active: 'ACTIVE_CHARACTER',
    CatCode.parameter: 'PARAMETER',
    CatCode.math_shift: 'MATH_SHIFT',
    CatCode.align_tab: 'ALIGN_TAB',
    CatCode.superscript: 'SUPERSCRIPT',
    CatCode.subscript: 'SUBSCRIPT',
}


literal_types = tuple(literals_map.values())
literal_types += tuple(non_active_literals_map.values())
literal_types += (other_literal_type,)
literal_types += tuple(category_map.values())
# Remove duplicates, since multiple literals map to the same type.
literal_types = tuple(set(literal_types))

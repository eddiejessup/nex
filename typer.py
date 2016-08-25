from common import TerminalToken
from lexer import CatCode


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

    ('\'', CatCode.other): 'SINGLE_QUOTE',
    ('"', CatCode.other): 'DOUBLE_QUOTE',
    ('`', CatCode.other): 'BACKTICK',
}

non_active_literals_map = {
    'b': 'NON_ACTIVE_b',
    'B': 'NON_ACTIVE_B',
    'y': 'NON_ACTIVE_y',
    'Y': 'NON_ACTIVE_Y',
}

other_literal_type = 'MISC_CHAR_CAT_PAIR'

category_map = {
    CatCode.space: 'SPACE',
    CatCode.begin_group: 'LEFT_BRACE',
    CatCode.end_group: 'RIGHT_BRACE',
    CatCode.active: 'ACTIVE_CHARACTER',
    CatCode.parameter: 'PARAMETER',
}


literal_types = tuple(literals_map.values())
literal_types += tuple(non_active_literals_map.values())
literal_types += (other_literal_type,)
literal_types += tuple(category_map.values())
literal_types = tuple(set(literal_types))


def get_char_cat_pair_terminal_type(char_cat_pair_token):
    v = char_cat_pair_token.value
    char, cat = v['char'], v['cat']
    if cat in (CatCode.letter, CatCode.other) and (char, cat) in literals_map:
        terminal_token_type = literals_map[(char, cat)]
    elif cat != CatCode.active and char in non_active_literals_map:
        terminal_token_type = non_active_literals_map[char]
    elif cat in (CatCode.letter, CatCode.other):
        terminal_token_type = other_literal_type
    elif cat in category_map:
        terminal_token_type = category_map[cat]
    else:
        import pdb; pdb.set_trace()
    return terminal_token_type


def char_cat_pair_to_terminal_token(char_cat_pair_token):
    terminal_token_type = get_char_cat_pair_terminal_type(char_cat_pair_token)
    terminal_token = TerminalToken(type_=terminal_token_type,
                                   value=char_cat_pair_token)
    return terminal_token
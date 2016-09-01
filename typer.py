from string import ascii_letters
from enum import Enum
from common import TerminalToken, InternalToken
from lexer import CatCode, char_cat_lex_type, control_sequence_lex_type


class PhysicalUnit(Enum):
    point = 'pt'
    pica = 'pc'
    inch = 'in'
    big_point = 'bp'
    centimetre = 'cm'
    millimetre = 'mm'
    didot_point = 'dd'
    cicero = 'cc'
    scaled_point = 'sp'
    fil = 'fil'


class MuUnit(Enum):
    mu = 'mu'


units_in_scaled_points = {}
units_in_scaled_points[PhysicalUnit.scaled_point] = 1
units_in_scaled_points[PhysicalUnit.point] = 65536 * units_in_scaled_points[PhysicalUnit.scaled_point]
units_in_scaled_points[PhysicalUnit.pica] = 12 * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.inch] = 72.27 * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.big_point] = (1.0 / 72.0) * units_in_scaled_points[PhysicalUnit.inch]
units_in_scaled_points[PhysicalUnit.centimetre] = (1.0 / 2.54) * units_in_scaled_points[PhysicalUnit.inch]
units_in_scaled_points[PhysicalUnit.millimetre] = 0.1 * units_in_scaled_points[PhysicalUnit.centimetre]
units_in_scaled_points[PhysicalUnit.didot_point] = (1238.0 / 1157.0) * units_in_scaled_points[PhysicalUnit.point]
units_in_scaled_points[PhysicalUnit.cicero] = 12 * units_in_scaled_points[PhysicalUnit.didot_point]

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

non_active_literals_map = {}
for c in ascii_letters:
    terminal_type = 'NON_ACTIVE_UNCASED_{}'.format(c.lower())
    non_active_literals_map[c] = terminal_type


other_literal_type = 'MISC_CHAR_CAT_PAIR'

category_map = {
    CatCode.space: 'SPACE',
    CatCode.begin_group: 'LEFT_BRACE',
    # TODO: This is not a terminal token.
    CatCode.end_group: 'RIGHT_BRACE',
    CatCode.active: 'ACTIVE_CHARACTER',
    # TODO: This is not a terminal token.
    CatCode.parameter: 'PARAMETER',
}


unexpanded_cs_type = 'UNEXPANDED_CONTROL_SEQUENCE'
unexpanded_one_char_cs_type = 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE'
unexpanded_cs_types = (unexpanded_cs_type, unexpanded_one_char_cs_type)


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


def make_char_cat_pair_terminal_token(char_cat_pair_token):
    terminal_token_type = get_char_cat_pair_terminal_type(char_cat_pair_token)
    value = char_cat_pair_token.value
    value['lex_type'] = char_cat_pair_token.type
    terminal_token = TerminalToken(type_=terminal_token_type,
                                   value=value)
    return terminal_token


def make_unexpanded_control_sequence_terminal_token(name):
    type_ = (unexpanded_one_char_cs_type if len(name) == 1
             else unexpanded_cs_type)
    # Convert to a primitive unexpanded control sequence.
    value = {'name': name, 'lex_type': control_sequence_lex_type}
    terminal_token = TerminalToken(type_=type_, value=value)
    return terminal_token


def lex_token_to_unexpanded_terminal_token(lex_token):
    # If we have a char-cat pair, we must type it to its terminal version,
    if lex_token.type == char_cat_lex_type:
        terminal_token = make_char_cat_pair_terminal_token(lex_token)
    elif lex_token.type == control_sequence_lex_type:
        name = lex_token.value
        terminal_token = make_unexpanded_control_sequence_terminal_token(name)
    elif isinstance(lex_token, InternalToken):
        terminal_token = lex_token
    return terminal_token


terminal_primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
    'sfcode': 'SPACE_FACTOR_CODE',
    'delcode': 'DELIMITER_CODE',

    'let': 'LET',

    'advance': 'ADVANCE',

    'par': 'PAR',
    'relax': 'RELAX',
    'immediate': 'IMMEDIATE',

    'message': 'MESSAGE',
    'errmessage': 'ERROR_MESSAGE',
    'write': 'WRITE',

    'global': 'GLOBAL',
    'long': 'LONG',
    'outer': 'OUTER',

    'expandafter': 'EXPAND_AFTER',

    'uppercase': 'UPPER_CASE',
    'lowercase': 'LOWER_CASE',
}


register_tokens = {
    'count': 'COUNT',
    'dimen': 'DIMEN',
    'skip': 'SKIP',
    'muskip': 'MU_SKIP',
}
terminal_primitive_control_sequences_map.update(register_tokens)

short_hand_def_map = {
    'chardef': 'CHAR_DEF',
    'mathchardef': 'MATH_CHAR_DEF',
    'countdef': 'COUNT_DEF',
    'dimendef': 'DIMEN_DEF',
    'skipdef': 'SKIP_DEF',
    'muskipdef': 'MU_SKIP_DEF',
    'toksdef': 'TOKS_DEF',
}
terminal_primitive_control_sequences_map.update(short_hand_def_map)

short_hand_def_to_token_map = {
    k: '{}_TOKEN'.format(k)
    for k in short_hand_def_map.values()
}

def_map = {
    'def': 'DEF',
    'gdef': 'G_DEF',
    'edef': 'E_DEF',
    'xdef': 'X_DEF',
}
terminal_primitive_control_sequences_map.update(def_map)

non_terminal_primitive_control_sequences_map = {
    'else': 'ELSE',
    'fi': 'END_IF',
    'string': 'STRING',
    'csname': 'CS_NAME',
    'endcsname': 'END_CS_NAME',
}

if_map = {
    'ifnum': 'IF_NUM',
    'iftrue': 'IF_TRUE',
    'iffalse': 'IF_FALSE',
}
non_terminal_primitive_control_sequences_map.update(if_map)

primitive_control_sequences_map = dict(**terminal_primitive_control_sequences_map,
                                       **non_terminal_primitive_control_sequences_map)


composite_terminal_control_sequence_types = (
    'BALANCED_TEXT_AND_RIGHT_BRACE',
    'PARAMETER_TEXT',
)


def type_primitive_control_sequence(call_token):
    name = call_token.value['name']
    # Terminals are tokens that may be passed to the parser.
    # Non-terminals are tokens that will be consumed by the banisher before the
    # parser sees them.
    is_terminal = name in terminal_primitive_control_sequences_map
    TokenCls = TerminalToken if is_terminal else InternalToken
    primitive_type = primitive_control_sequences_map[name]
    primitive_token = TokenCls(type_=primitive_type, value=call_token.value)
    return primitive_token

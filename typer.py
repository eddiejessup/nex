from collections import namedtuple
from string import ascii_letters
from enum import Enum

from common import TerminalToken, InternalToken


cat_codes = [
    'escape',  # 0
    'begin_group',  # 1
    'end_group',  # 2
    'math_shift',  # 3
    'align_tab',  # 4
    'end_of_line',  # 5
    'parameter',  # 6
    'superscript',  # 7
    'subscript',  # 8
    'ignored',  # 9
    'space',  # 10
    'letter',  # 11
    'other',  # 12
    'active',  # 13
    'comment',  # 14
    'invalid',  # 15
]

CatCode = Enum('CatCode', {symbol: i for i, symbol in enumerate(cat_codes)})


weird_char_codes = {
    'null': 0,
    'line_feed': 10,
    'carriage_return': 13,
    'delete': 127,
}
weird_chars = {
    k: chr(v) for k, v in weird_char_codes.items()
}
WeirdChar = Enum('WeirdChar', weird_chars)


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


char_cat_lex_type = 'CHAR_CAT_PAIR'
control_sequence_lex_type = 'CONTROL_SEQUENCE'


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


unexpanded_token_type = 'UNEXPANDED_TOKEN'
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

    'font': 'FONT',

    # Font assignment things.
    'skewchar': 'SKEW_CHAR',
    'hyphenchar': 'HYPHEN_CHAR',
    'fontdimen': 'FONT_DIMEN',

    # Font ranges.
    'textfont': 'TEXT_FONT',
    'scriptfont': 'SCRIPT_FONT',
    'scriptscriptfont': 'SCRIPT_SCRIPT_FONT',

    'undefined': 'UNDEFINED',

    # Macro modifiers.
    'global': 'GLOBAL',
    'long': 'LONG',
    'outer': 'OUTER',

    # Box related things.

    # Box register assignment.
    'setbox': 'SET_BOX',
    # Box register calls.
    # This one deletes the register contents when called.
    'box': 'BOX',
    # This one does not.
    'copy': 'COPY',

    # Remove and return (pop) the most recent h- or v-box, if any.
    'lastbox': 'LAST_BOX',
    # Make a vbox by splitting off a certain amount of material from a box
    # register.
    'vsplit': 'V_SPLIT',

}


explicit_box_map = {
    'hbox': 'H_BOX',
    'vbox': 'V_BOX',
    # Like 'vbox', but its baseline is that of the top box inside,
    # rather than the bottom box inside.
    'vtop': 'V_TOP',
}
terminal_primitive_control_sequences_map.update(explicit_box_map)


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
    'toksdef': 'TOKS_DEF',
}
short_hand_def_register_map = {
    '{}def'.format(k): '{}_DEF'.format(v) for k, v in register_tokens.items()
}
short_hand_def_map.update(short_hand_def_register_map)
terminal_primitive_control_sequences_map.update(short_hand_def_map)

short_hand_def_to_token_map = {
    v: '{}_TOKEN'.format(v)
    for v in short_hand_def_map.values()
}
font_def_token_type = 'FONT_DEF_TOKEN'

def_map = {
    'def': 'DEF',
    'gdef': 'G_DEF',
    'edef': 'E_DEF',
    'xdef': 'X_DEF',
}
terminal_primitive_control_sequences_map.update(def_map)

non_terminal_primitive_control_sequences_map = {
    'string': 'STRING',
    'csname': 'CS_NAME',
    'endcsname': 'END_CS_NAME',

    'expandafter': 'EXPAND_AFTER',

    'uppercase': 'UPPER_CASE',
    'lowercase': 'LOWER_CASE',

    'cr': 'CR',
}

condition_tokens_map = {
    'else': 'ELSE',
    'fi': 'END_IF',
    'or': 'OR',
}
non_terminal_primitive_control_sequences_map.update(condition_tokens_map)
if_map = {
    'ifnum': 'IF_NUM',
    'iftrue': 'IF_TRUE',
    'iffalse': 'IF_FALSE',
    'ifcase': 'IF_CASE',
}
non_terminal_primitive_control_sequences_map.update(if_map)

primitive_control_sequences_map = dict(**terminal_primitive_control_sequences_map,
                                       **non_terminal_primitive_control_sequences_map)


composite_terminal_control_sequence_types = (
    'BALANCED_TEXT_AND_RIGHT_BRACE',
    'PARAMETER_TEXT',
    'HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE',
    'VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE',
)

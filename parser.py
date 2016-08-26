import logging

from utils import post_mortem
from common import Token, TerminalToken
from lexer import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander, parse_replacement_text
from registers import registers
from common_parsing import pg as common_pg, evaluate_number, evaluate_dimen

from expander import short_hand_def_map


short_hand_def_to_token_map = {
    k: '{}_TOKEN'.format(k)
    for k in short_hand_def_map.values()
}


# tokens = ()
# tokens += tuple(terminal_primitive_control_sequences_map.values())
# tokens += tuple(short_hand_def_to_token_map.values())
# tokens += tuple(literal_types)
# tokens += tuple(special_terminal_control_sequence_types)
# tokens = tuple(set(tokens))

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


# prec = (
#     ('left', 'SPACE'),
#     # ('left', 'UNEXPANDED_CONTROL_SEQUENCE'),
# )


pg = common_pg.copy_to_extend()


@pg.production('commands : commands command')
def commands_extend(parser_state, p):
    v = p[0]
    v.append(p[1])
    return v


@pg.production('commands : command')
def commands(parser_state, p):
    return [p[0]]


@pg.production('command : assignment')
@pg.production('command : character')
@pg.production('command : PAR')
@pg.production('command : SPACE')
@pg.production('command : message')
@pg.production('command : write')
@pg.production('command : RELAX')
def command(parser_state, p):
    return p[0]


@pg.production('assignment : macro_assignment')
@pg.production('assignment : non_macro_assignment')
def assignment(parser_state, p):
    return p[0]


@pg.production('write : IMMEDIATE write')
def immediate_write(parser_state, p):
    return p[1]
    p[0].value['prefix'] = 'immediate'


@pg.production('write : WRITE number general_text')
def write(parser_state, p):
    return Token(type_='write',
                 value={'stream_number': p[1], 'content': p[2]})


@pg.production('message : ERROR_MESSAGE general_text')
@pg.production('message : MESSAGE general_text')
def message(parser_state, p):
    return Token(type_='message',
                 value={'content': p[1]})


@pg.production('general_text : filler implicit_left_brace BALANCED_TEXT RIGHT_BRACE')
def general_text(parser_state, p):
    return p[2]


@pg.production('filler : optional_spaces')
@pg.production('filler : filler RELAX optional_spaces')
def filler(parser_state, p):
    return None


@pg.production('implicit_left_brace : LEFT_BRACE')
def implicit_left_brace(parser_state, p):
    return p[0]


@pg.production('macro_assignment : prefix macro_assignment')
def macro_assignment_prefix(parser_state, p):
    v = p[1]
    # TODO: actually do something about this in expander.
    v.value['prefixes'].add(p[0])
    return v


@pg.production('prefix : GLOBAL')
@pg.production('prefix : LONG')
@pg.production('prefix : OUTER')
def prefix(parser_state, p):
    return p[0].type


@pg.production('macro_assignment : definition')
def macro_assignment(parser_state, p):
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': p[0]})
    name = p[0].value['name']
    parser_state.e.control_sequences[name] = macro_token
    return macro_token


@pg.production('definition : DEF control_sequence definition_text')
def definition(parser_state, p):
    def_token = Token(type_='definition',
                      value={'name': p[1].value['name'],
                             'text': p[2]})
    return def_token


@pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT RIGHT_BRACE')
def definition_text(parser_state, p):
    # TODO: maybe move this parsing logic to inside the Expander.
    replacement_text = parse_replacement_text(p[2].value)
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': p[0].value,
                                  'replacement_text': replacement_text})
    return def_text_token


@pg.production('non_macro_assignment : GLOBAL non_macro_assignment')
def non_macro_assignment_global(parser_state, p):
    v = p[1]
    v.value['global'] = True
    return v


@pg.production('non_macro_assignment : simple_assignment')
def non_macro_assignment(parser_state, p):
    return p[0]


@pg.production('simple_assignment : variable_assignment')
@pg.production('simple_assignment : arithmetic')
@pg.production('simple_assignment : code_assignment')
@pg.production('simple_assignment : let_assignment')
@pg.production('simple_assignment : short_hand_definition')
def simple_assignment(parser_state, p):
    return p[0]


@pg.production('variable_assignment : glue_variable equals glue')
def variable_assignment_glue(parser_state, p):
    glue = p[2]
    evaluated_glue = {}
    for k in ('dimen', 'stretch', 'shrink'):
        dimen = glue[k]
        if dimen is None:
            evaluated_dimen = None
        else:
            evaluated_dimen = evaluate_dimen(dimen)
        evaluated_glue[k] = evaluated_dimen
    # TODO: Could also be a glue parameter.
    if p[0].type == 'glue':
        registers.skip[p[0].value] = evaluated_glue
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('variable_assignment : dimen_variable equals dimen')
def variable_assignment_dimen(parser_state, p):
    value = evaluate_dimen(p[2])
    # TODO: Could also be a dimen parameter.
    if p[0].type == 'dimen':
        registers.dimen[p[0].value] = value
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('variable_assignment : integer_variable equals number')
def variable_assignment_integer(parser_state, p):
    value = evaluate_number(p[2])
    # TODO: Could also be a count parameter.
    if p[0].type == 'count':
        try:
            registers.count[p[0].value] = value
        except TypeError:
            import pdb; pdb.set_trace()
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('arithmetic : ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(parser_state, p):
    value = evaluate_number(p[3])
    if p[1].type == 'count':
        registers.count[p[1].value] += value
    return Token(type_='advance', value={'target': p[1], 'value': p[3]})


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(parser_state, p):
    return None


@pg.production('short_hand_definition : short_hand_def control_sequence equals number')
def short_hand_definition(parser_state, p):
    code = evaluate_number(p[3])
    def_type = p[0].type
    def_token_type = short_hand_def_to_token_map[def_type]
    primitive_token = TerminalToken(type_=def_token_type, value=code)
    control_sequence_name = p[1].value['name']
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': [],
                                  'replacement_text': [primitive_token]})
    def_token = Token(type_='definition',
                      value={'name': control_sequence_name,
                             'text': def_text_token})
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': def_token})
    parser_state.e.control_sequences[control_sequence_name] = macro_token
    # Just for the sake of output.
    return macro_token


@pg.production('let_assignment : LET control_sequence equals one_optional_space control_sequence')
def let_assignment_control_sequence(parser_state, p):
    # TODO allow char_cat_pair.
    target_name = p[4].value['name']
    target_contents = parser_state.e.control_sequences[target_name]
    new_name = p[1].value['name']
    parser_state.e.control_sequences[new_name] = target_contents
    return Token(type_='let_assignment',
                 value={'name': new_name,
                        'target_name': target_name,
                        'target_contents': target_contents})


@pg.production('short_hand_def : CHAR_DEF')
@pg.production('short_hand_def : MATH_CHAR_DEF')
@pg.production('short_hand_def : COUNT_DEF')
@pg.production('short_hand_def : DIMEN_DEF')
@pg.production('short_hand_def : SKIP_DEF')
@pg.production('short_hand_def : MU_SKIP_DEF')
@pg.production('short_hand_def : TOKS_DEF')
def short_hand_def(parser_state, p):
    return p[0]


def split_at(s, inds):
    inds = [0] + list(inds) + [len(s)]
    return [s[inds[i]:inds[i + 1]] for i in range(0, len(inds) - 1)]


def split_hex_code(n, hex_length, inds):
    # Get the zero-padded string representation of the number in base 16.
    n_hex = format(n, '0{}x'.format(hex_length))
    # Check the number is of the correct magnitude.
    assert len(n_hex) == hex_length
    # Split the hex string into pieces, at the given indices.
    parts_hex = split_at(n_hex, inds)
    # Convert each part from hex to decimal.
    parts = [int(part, base=16) for part in parts_hex]
    return parts


@pg.production('code_assignment : code_name number equals number')
def code_assignment(parser_state, p):
    code_type, char_number, code_number = p[0], p[1], p[3]
    char_size, code_size = evaluate_number(char_number), evaluate_number(code_number)
    char = chr(char_size)
    code_type_to_char_map = {
        'CAT_CODE': parser_state.lex.char_to_cat,
        'MATH_CODE': parser_state.lex.char_to_math_code,
        'UPPER_CASE_CODE': parser_state.lex.upper_case_code,
        'LOWER_CASE_CODE': parser_state.lex.lower_case_code,
        'SPACE_FACTOR_CODE': parser_state.lex.space_factor_code,
        'DELIMITER_CODE': parser_state.lex.delimiter_code,
    }
    if code_type == 'CAT_CODE':
        code = CatCode(code_size)
    elif code_type == 'MATH_CODE':
        parts = split_hex_code(code_size, hex_length=4, inds=(1, 2))
        math_class_i, family, position = parts
        math_class = MathClass(math_class_i)
        glyph_code = GlyphCode(family, position)
        code = MathCode(math_class, glyph_code)
    elif code_type in ('UPPER_CASE_CODE', 'LOWER_CASE_CODE'):
        code = chr(code_size)
    elif code_type == 'SPACE_FACTOR_CODE':
        code = code_size
    elif code_type == 'DELIMITER_CODE':
        parts = split_hex_code(code_size, hex_length=6, inds=(1, 3, 4))
        small_family, small_position, large_family, large_position = parts
        small_glyph_code = GlyphCode(small_family, small_position)
        large_glyph_code = GlyphCode(large_family, large_position)
        code = DelimiterCode(small_glyph_code, large_glyph_code)
    char_map = code_type_to_char_map[code_type]
    char_map[char] = code
    return {'type': 'code_assignment', 'code_type': code_type,
            'char': char, 'code': code}


@pg.production('code_name : CAT_CODE')
@pg.production('code_name : MATH_CODE')
@pg.production('code_name : UPPER_CASE_CODE')
@pg.production('code_name : LOWER_CASE_CODE')
@pg.production('code_name : SPACE_FACTOR_CODE')
@pg.production('code_name : DELIMITER_CODE')
def code_name_cat(parser_state, p):
    return p[0].type


@pg.error
def error(parser_state, p):
    print("Syntax error in input!")
    post_mortem(parser_state, parser)
    raise ValueError

# Build the parser
parser = pg.build()


class LexWrapper(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.r = Reader(file_name)
        self.lex = Lexer(self.r)
        self.e = Expander()
        self.b = Banisher(self.lex, self.e)

    def __next__(self):
        try:
            return self.b.next_token
        except EndOfFile:
            return None

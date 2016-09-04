import logging

from utils import post_mortem
from typer import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from common import Token
from state import GlobalState
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander, parse_replacement_text, parameter_types
from fonts import FontRange, FontState
from registers import is_register_type
from common_parsing import (pg as common_pg,
                            evaluate_number, evaluate_dimen, evaluate_glue)
from general_text_parser import gen_txt_pg


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


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


pg.add_recent_productions(gen_txt_pg)


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
    name = p[0].value['name']
    macro_token = parser_state.state.set_macro(name, p[0], prefixes=None)
    return macro_token


@pg.production('definition : def control_sequence definition_text')
def definition(parser_state, p):
    def_token = Token(type_='definition',
                      value={'def_type': p[0],
                             'name': p[1].value['name'],
                             'text': p[2]})
    return def_token


# TODO: can automate this, and many like it, using expander maps.
@pg.production('def : DEF')
@pg.production('def : G_DEF')
@pg.production('def : E_DEF')
@pg.production('def : X_DEF')
def def_(parser_state, p):
    return p[0]


@pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
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
@pg.production('simple_assignment : family_assignment')
@pg.production('simple_assignment : set_box_assignment')
@pg.production('simple_assignment : font_definition')
@pg.production('simple_assignment : global_assignment')
def simple_assignment(parser_state, p):
    return p[0]


@pg.production('simple_assignment : FONT_DEF_TOKEN')
def simple_assignment_font_selection(parser_state, p):
    font_id = p[0].value
    parser_state.state.set_current_font(font_id)
    return Token(type_='font_selection', value=font_id)


@pg.production('family_assignment : family_member equals font')
def family_assignment(parser_state, p):
    # TODO: will this work for productions of font other than FONT_DEF_TOKEN?
    font_id = p[2].value
    font_range = p[0].type
    family_nr = evaluate_number(parser_state, p[0].value)
    parser_state.state.set_font_family(family_nr, font_range, font_id)
    return Token(type_='family_assignment',
                 value={'family_nr': family_nr,
                        'font_range': font_range,
                        'font_id': font_id})


@pg.production('set_box_assignment : SET_BOX number equals filler box')
def set_box_assignment(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('font_definition : FONT control_sequence equals optional_spaces file_name filler at_clause')
def font_definition(parser_state, p):
    file_name, at_clause = p[4], p[6]
    control_sequence_name = p[1].value['name']
    macro_token = parser_state.state.define_new_font(control_sequence_name,
                                                     file_name,
                                                     at_clause)
    return macro_token


@pg.production('file_name : character')
@pg.production('file_name : file_name character')
def file_name(parser_state, p):
    if len(p) > 1:
        return p[0] + p[1].value['char']
    else:
        return p[0].value['char']


@pg.production('at_clause : at dimen')
def at_clause_dimen(parser_state, p):
    return Token(type_='at_dimen', value=p[1])


@pg.production('at_clause : scaled number')
def at_clause_scaled(parser_state, p):
    return Token(type_='scaled_number', value=p[1])


@pg.production('at_clause : optional_spaces')
def at_clause_empty(parser_state, p):
    return None


@pg.production('box : BOX number')
@pg.production('box : COPY number')
@pg.production('box : LAST_BOX')
@pg.production('box : V_SPLIT number to dimen')
@pg.production('box : H_BOX box_specification LEFT_BRACE HORIZONTAL_MODE_MATERIAL RIGHT_BRACE')
@pg.production('box : V_BOX box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL RIGHT_BRACE')
@pg.production('box : V_TOP box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL RIGHT_BRACE')
def box(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('box_specification : to dimen filler')
@pg.production('box_specification : spread dimen filler')
@pg.production('box_specification : filler')
def box_specification(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('global_assignment : font_assignment')
# @pg.production('global_assignment : hyphenation_assignment')
# @pg.production('global_assignment : box_size_assignment')
# @pg.production('global_assignment : interaction_mode_assignment')
# @pg.production('global_assignment : intimate_assignment')
def global_assignment(parser_state, p):
    return p[0]


# @pg.production('font_assignment : FONT_DIMEN number font equals dimen')
@pg.production('font_assignment : HYPHEN_CHAR font equals number')
def font_assignment_hyphen(parser_state, p):
    # TODO: can we make this nicer by storing the char instead of the number?
    evaluated_number = evaluate_number(parser_state, p[3])
    # TODO: as for font definition, does this work for non-FONT_DEF_TOKEN font
    # productions?
    font_id = p[1].value
    parser_state.state.global_font_state.set_hyphen_char(font_id, evaluated_number)
    return Token(type_='skew_char_assignment',
                 value={'font_id': font_id, 'code': p[3]})


@pg.production('font_assignment : SKEW_CHAR font equals number')
def font_assignment_skew(parser_state, p):
    # TODO: can we make this nicer by storing the char instead of the number?
    evaluated_number = evaluate_number(parser_state, p[3])
    # TODO: as for font definition, does this work for non-FONT_DEF_TOKEN font
    # productions?
    font_id = p[1].value
    parser_state.state.global_font_state.set_skew_char(font_id, evaluated_number)
    return Token(type_='skew_char_assignment',
                 value={'font_id': font_id, 'code': p[3]})


@pg.production('font : FONT_DEF_TOKEN')
# @pg.production('font : family_member')
# @pg.production('font : FONT')
def font(parser_state, p):
    return p[0]


@pg.production('family_member : font_range number')
def family_member(parser_state, p):
    return Token(type_=p[0], value=p[1])


@pg.production('font_range : TEXT_FONT')
@pg.production('font_range : SCRIPT_FONT')
@pg.production('font_range : SCRIPT_SCRIPT_FONT')
def font_range(parser_state, p):
    return FontRange(p[0].type)


def do_variable_assignment(parser_state, variable, value):
    if is_register_type(variable.type):
        parser_state.state.set_register_value(variable.type,
                                              i=variable.value,
                                              value=value)
    elif variable.type in parameter_types:
        param_name = variable.value['canonical_name']
        parser_state.state.set_parameter(name=param_name, value=value)


@pg.production('variable_assignment : mu_glue_variable equals mu_glue')
@pg.production('variable_assignment : glue_variable equals glue')
def variable_assignment_glue(parser_state, p):
    glue = p[2]
    evaluated_glue = evaluate_glue(parser_state, glue)
    do_variable_assignment(parser_state, p[0], evaluated_glue)
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('variable_assignment : dimen_variable equals dimen')
def variable_assignment_dimen(parser_state, p):
    evaluated_dimen = evaluate_dimen(parser_state, p[2])
    do_variable_assignment(parser_state, p[0], evaluated_dimen)
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('variable_assignment : integer_variable equals number')
def variable_assignment_integer(parser_state, p):
    evaluated_number = evaluate_number(parser_state, p[2])
    do_variable_assignment(parser_state, p[0], evaluated_number)
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('arithmetic : ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(parser_state, p):
    value = evaluate_number(parser_state, p[3])
    if is_register_type(p[1].type):
        parser_state.state.advance_register_value(p[1].type,
                                                  i=p[1].value,
                                                  value=value)
    return Token(type_='advance', value={'target': p[1], 'value': p[3]})


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(parser_state, p):
    return None


@pg.production('short_hand_definition : short_hand_def control_sequence equals number')
def short_hand_definition(parser_state, p):
    code = evaluate_number(parser_state, p[3])
    def_type = p[0].type
    control_sequence_name = p[1].value['name']
    macro_token = parser_state.state.do_short_hand_definition(control_sequence_name,
                                                              def_type,
                                                              code)
    # Just for the sake of output.
    return macro_token


@pg.production('let_assignment : LET control_sequence equals one_optional_space UNEXPANDED_TOKEN')
def let_assignment_control_sequence(parser_state, p):
    target_token = p[4].value
    new_name = p[1].value['name']
    parser_state.state.do_let_assignment(new_name, target_token)
    return Token(type_='let_assignment',
                 value={'name': new_name,
                        'target_name': target_token})


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
    char_size, code_size = evaluate_number(parser_state, char_number), evaluate_number(parser_state, code_number)
    char = chr(char_size)
    code_type_to_func_map = {
        'CAT_CODE': parser_state.state.set_cat_code,
        'MATH_CODE': parser_state.state.set_math_code,
        'UPPER_CASE_CODE': parser_state.state.set_lower_case_code,
        'LOWER_CASE_CODE': parser_state.state.set_upper_case_code,
        'SPACE_FACTOR_CODE': parser_state.state.set_space_factor_code,
        'DELIMITER_CODE': parser_state.state.set_delimiter_code,
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
    set_func = code_type_to_func_map[code_type]
    set_func(char, code)
    return Token(type_='code_assignment',
                 value={'code_type': code_type, 'char': char, 'code': code})


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
        self.state = GlobalState()
        self.file_name = file_name
        self.r = Reader(file_name)
        self.lex = Lexer(self.r, self.state)
        self.b = Banisher(self.lex, wrapper=self)

    def __next__(self):
        try:
            return self.b.next_token
        except EndOfFile:
            return None

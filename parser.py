from collections import deque
import logging

from reader import EndOfFile
from utils import post_mortem
from typer import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from common import Token
from expander import parse_replacement_text, parameter_types
from fonts import FontRange
from registers import is_register_type
from common_parsing import (pg as common_pg,
                            evaluate_number, evaluate_dimen, evaluate_glue)
from parse_utils import ExpectedParsingError, ExhaustedTokensError, is_end_token
from general_text_parser import gen_txt_pg


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


pg = common_pg.copy_to_extend()


# @pg.production('commands : commands command')
# def commands_extend(parser_state, p):
#     v = p[0]
#     v.append(p[1])
#     return v


# @pg.production('commands : command')
# def commands(parser_state, p):
#     return [p[0]]


@pg.production('command : assignment')
@pg.production('command : add_kern')
@pg.production('command : add_glue')
@pg.production('command : character')
@pg.production('command : PAR')
@pg.production('command : SPACE')
@pg.production('command : message')
@pg.production('command : write')
@pg.production('command : RELAX')
@pg.production('command : box')
@pg.production('command : vertical_rule')
@pg.production('command : horizontal_rule')
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


@pg.production('macro_assignment : prefixes definition')
def macro_assignment_prefix(parser_state, p):
    prefixes = p[0]
    definition_token = p[1]
    name = definition_token.value['name']
    macro_token = parser_state.state.set_macro(name, definition_token,
                                               prefixes=prefixes)
    return macro_token


@pg.production('prefixes : prefix')
@pg.production('prefixes : prefixes prefix')
def prefix(parser_state, p):
    if len(p) > 1:
        return p[0] + [p[1]]
    else:
        return [p[0]]


@pg.production('prefixes : empty')
def prefix(parser_state, p):
    return []


@pg.production('prefix : GLOBAL')
@pg.production('prefix : LONG')
@pg.production('prefix : OUTER')
def prefix(parser_state, p):
    return p[0].type


# @pg.production('macro_assignment : definition')
# def macro_assignment(parser_state, p):
#     macro_token = Token(type_='macro',
#                         value={'prefixes': set(),
#                                'definition': p[0]})
#     return macro_token


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


# Start of 'variable assignment', a simple assignment.

@pg.production('simple_assignment : optional_globals variable_assignment')
def simple_assignment_variable(parser_state, p):
    return p[0]


@pg.production('variable_assignment : optional_globals evaluated_variable_assignment')
def variable_assignment(parser_state, p):
    is_global = p[0]
    variable, value = p[1]
    if is_register_type(variable.type):
        parser_state.state.set_register_value(is_global=is_global,
                                              type_=variable.type,
                                              i=variable.value,
                                              value=value)
    elif variable.type in parameter_types:
        param_name = variable.value['canonical_name']
        parser_state.state.set_parameter(is_global=is_global,
                                         name=param_name, value=value)
    return Token(type_='variable_assignment',
                 value={'variable': variable, 'value': value})


@pg.production('evaluated_variable_assignment : mu_glue_variable equals mu_glue')
@pg.production('evaluated_variable_assignment : glue_variable equals glue')
def variable_assignment_glue(parser_state, p):
    return [p[0], evaluate_glue(parser_state, p[2])]


@pg.production('evaluated_variable_assignment : dimen_variable equals dimen')
def variable_assignment_dimen(parser_state, p):
    return [p[0], evaluate_dimen(parser_state, p[2])]


@pg.production('evaluated_variable_assignment : integer_variable equals number')
def variable_assignment_integer(parser_state, p):
    return [p[0], evaluate_number(parser_state, p[2])]


# End of 'variable assignment', a simple assignment.

# Start of 'arithmetic', a simple assignment.


@pg.production('arithmetic : optional_globals ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(parser_state, p):
    is_global = p[0]
    value = evaluate_number(parser_state, p[4])
    if is_register_type(p[2].type):
        parser_state.state.advance_register_value(is_global=is_global,
                                                  type_=p[2].type,
                                                  i=p[2].value,
                                                  value=value)
    else:
        import pdb; pdb.set_trace()
    # TODO: Allow arithmetic on parameters.
    # TODO: Allow multiply and divide operations.
    # TODO: Allow arithmetic on dimen, glue and muglue.
    return Token(type_='advance', value={'target': p[2], 'value': p[4]})


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(parser_state, p):
    return None


# End of 'arithmetic', a simple assignment.

# Start of 'code assignment', a simple assignment.


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


@pg.production('code_assignment : optional_globals code_name number equals number')
def code_assignment(parser_state, p):
    is_global = p[0]
    code_type, char_number, code_number = p[1], p[2], p[4]
    char_size, code_size = evaluate_number(parser_state, char_number), evaluate_number(parser_state, code_number)
    char = chr(char_size)
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
    parser_state.state.set_code(is_global, code_type, char, code)
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


# End of 'code assignment', a simple assignment.

# Start of 'let assignment', a simple assignment.


@pg.production('let_assignment : optional_globals LET control_sequence equals one_optional_space UNEXPANDED_TOKEN')
def let_assignment_control_sequence(parser_state, p):
    is_global = p[0]
    target_token = p[5].value
    new_name = p[2].value['name']
    parser_state.state.do_let_assignment(is_global, new_name, target_token)
    return Token(type_='let_assignment',
                 value={'name': new_name,
                        'target_name': target_token})


# End of 'let assignment', a simple assignment.

# Start of 'short-hand definition', a simple assignment.


@pg.production('short_hand_definition : optional_globals short_hand_def control_sequence equals number')
def short_hand_definition(parser_state, p):
    is_global = p[0]
    code = evaluate_number(parser_state, p[4])
    def_type = p[1].type
    control_sequence_name = p[2].value['name']
    macro_token = parser_state.state.do_short_hand_definition(is_global,
                                                              control_sequence_name,
                                                              def_type,
                                                              code)
    # Just for the sake of output.
    return macro_token


@pg.production('short_hand_def : CHAR_DEF')
@pg.production('short_hand_def : MATH_CHAR_DEF')
@pg.production('short_hand_def : COUNT_DEF')
@pg.production('short_hand_def : DIMEN_DEF')
@pg.production('short_hand_def : SKIP_DEF')
@pg.production('short_hand_def : MU_SKIP_DEF')
@pg.production('short_hand_def : TOKS_DEF')
def short_hand_def(parser_state, p):
    return p[0]


# End of 'short-hand definition', a simple assignment.

# Start of 'family assignment', a simple assignment.


@pg.production('family_assignment : optional_globals family_member equals font')
def family_assignment(parser_state, p):
    is_global = p[0]
    # TODO: will this work for productions of font other than FONT_DEF_TOKEN?
    font_id = p[3].value
    font_range = p[1].type
    family_nr = evaluate_number(parser_state, p[1].value)
    parser_state.state.set_font_family(is_global, family_nr, font_range, font_id)
    return Token(type_='family_assignment',
                 value={'family_nr': family_nr,
                        'font_range': font_range,
                        'font_id': font_id})


@pg.production('family_member : font_range number')
def family_member(parser_state, p):
    return Token(type_=p[0], value=p[1])


@pg.production('font_range : TEXT_FONT')
@pg.production('font_range : SCRIPT_FONT')
@pg.production('font_range : SCRIPT_SCRIPT_FONT')
def font_range(parser_state, p):
    return FontRange(p[0].type)


# End of 'family assignment', a simple assignment.

# Start of 'set box assignment', a simple assignment.


@pg.production('set_box_assignment : optional_globals SET_BOX number equals filler box')
def set_box_assignment(parser_state, p):
    is_global = p[0]
    # TODO: Actually put these contents in a register.
    return Token(type_='set_box_assignment',
                 value={'is_global': is_global, 'nr': p[2], 'contents': p[5]})


# @pg.production('box : BOX number')
# @pg.production('box : COPY number')
# @pg.production('box : LAST_BOX')
# @pg.production('box : V_SPLIT number to dimen')
@pg.production('box : H_BOX box_specification LEFT_BRACE HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE')
# @pg.production('box : V_BOX box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
# @pg.production('box : V_TOP box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
def box(parser_state, p):
    return Token(type_='h_box', value={'specification': p[1],
                                       'contents': p[3]})


@pg.production('box_specification : to dimen filler')
def box_specification_to(parser_state, p):
    return Token(type_='to', value=p[1])


@pg.production('box_specification : spread dimen filler')
def box_specification_spread(parser_state, p):
    return Token(type_='spread', value=p[1])


@pg.production('box_specification : filler')
def box_specification_empty(parser_state, p):
    return None


# End of 'set box assignment', a simple assignment.

# Start of 'font definition', a simple assignment.


@pg.production('font_definition : optional_globals FONT control_sequence equals optional_spaces file_name filler at_clause')
def font_definition(parser_state, p):
    is_global = p[0]
    file_name, at_clause = p[5], p[7]
    control_sequence_name = p[2].value['name']
    macro_token = parser_state.state.define_new_font(is_global,
                                                     control_sequence_name,
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


# End of 'font definition', a simple assignment.

# Start of 'global assignment', a simple assignment.


@pg.production('global_assignment : optional_globals global_assignment')
def global_assignment(parser_state, p):
    # Global prefixes have no effect.
    return p[1]


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


# End of 'global assignment', a simple assignment.


@pg.production('optional_globals : optional_globals GLOBAL')
def optional_globals_extend(parser_state, p):
    return True


@pg.production('optional_globals : GLOBAL')
@pg.production('optional_globals : empty')
def optional_globals(parser_state, p):
    return bool(p[0])


# End of the simple assignments.


@pg.production('add_kern : KERN dimen')
@pg.production('add_kern : MATH_KERN mu_dimen')
def add_kern(parser_state, p):
    return Token(type_=p[0].type, value=p[1])


@pg.production('add_glue : H_FIL')
@pg.production('add_glue : H_FILL')
@pg.production('add_glue : H_STRETCH_OR_SHRINK')
@pg.production('add_glue : H_FIL_NEG')
@pg.production('add_glue : V_FIL')
@pg.production('add_glue : V_FILL')
@pg.production('add_glue : V_STRETCH_OR_SHRINK')
@pg.production('add_glue : V_FIL_NEG')
def add_special_glue(parser_state, p):
    return Token(type_=p[0], value=None)


@pg.production('add_glue : H_SKIP glue')
@pg.production('add_glue : V_SKIP glue')
def add_glue(parser_state, p):
    return Token(type_=p[0], value=p[1])


@pg.production('vertical_rule : V_RULE rule_specification')
@pg.production('horizontal_rule : H_RULE rule_specification')
def rule(parser_state, p):
    return Token(type_=p[0], value=p[1])


@pg.production('rule_specification : rule_dimension rule_specification')
def rule_specification(parser_state, p):
    t = p[1]
    # TODO: does this give the correct overwrite order?
    # Presumably, repeating the same axis should obey the last one.
    dim_type = p[0].value['axis']
    t.value[dim_type] = p[0].value['dimen']
    return t


@pg.production('rule_specification : optional_spaces')
def rule_specification_empty(parser_state, p):
    dims = {'width': None, 'height': None, 'depth': None}
    return Token(type_='rule_specification', value=dims)


# TODO: these literals are getting unclear. Introduce some convention to make
# clear which (non-terminal) tokens represent literals.
@pg.production('rule_dimension : width dimen')
@pg.production('rule_dimension : height dimen')
@pg.production('rule_dimension : depth dimen')
def rule_dimension(parser_state, p):
    return Token(type_='rule_dimension',
                 value={'axis': p[0], 'dimen': p[1]})


@pg.error
def error(parser_state, look_ahead):
    # If we have exhausted the list of tokens while still
    # having a valid command, we should read more tokens until we get a syntax
    # error.
    if is_end_token(look_ahead):
        raise ExhaustedTokensError
    # Assume we have an actual syntax error, which we interpret to mean the
    # current command has finished being parsed and we are looking at tokens
    # for the next command.
    elif look_ahead is not None:
        raise ExpectedParsingError
    else:
        import pdb; pdb.set_trace()
    # if parser_state.in_recovery_mode:
    #     print("Syntax error in input!")
    #     post_mortem(parser_state, parser)
    #     raise ValueError

# Build the parser
parser = pg.build()


class CommandGrabber(object):

    def __init__(self, banisher, lex_wrapper, parser):
        self.banisher = banisher
        self.lex_wrapper = lex_wrapper
        self.parser = parser

        # Processing input tokens might return many tokens, so
        # we store them in a buffer.
        self.buffer_stack = deque()

        self.max_nr_extra_tokens = 1

    def get_command(self):
        # Want to extend the stack-to-be-parsed one token at a time,
        # so we can break as soon as we have all we need.
        parse_stack = deque()
        # Get enough tokens to evaluate command. We know to stop adding tokens
        # when we see a switch from failing because we run out of tokens
        # (ExhaustedTokensError) to an actual syntax error
        # (ExpectedParsingError).
        # We keep track of if we have parsed, just for checking for weird
        # situations.
        have_parsed = False
        while True:
            try:
                t = self.banisher.pop_or_fill_and_pop(self.buffer_stack)
            except EndOfFile:
                if have_parsed:
                    break
                # If we get an EndOfFile, and we have just started trying to
                # get a command, we are done, so just return.
                elif not parse_stack:
                    raise
                # If we get to the end of the file in the middle of a command,
                # something is wrong.
                else:
                    import pdb; pdb.set_trace()
                # if parse_stack:
                #     self.lex_wrapper.in_recovery_mode = True
                #     parser.parse(iter(parse_stack), state=self.lex_wrapper)
                #     import pdb; pdb.set_trace()
            parse_stack.append(t)
            try:
                result = self.parser.parse(iter(parse_stack),
                                           state=self.lex_wrapper)
            except ExpectedParsingError:
                if have_parsed:
                    # We got so many tokens of fluff due to extra reads,
                    # to make the parse stack not-parse.
                    # Put them back on the buffer.
                    self.buffer_stack.appendleft(parse_stack.pop())
                    break
                else:
                    import pdb; pdb.set_trace()
            except ExhaustedTokensError:
                # Carry on getting more tokens, because it seems we can.
                pass
            else:
                have_parsed = True
        return result

    def get_commands_until_end(self):
        commands = []
        while True:
            try:
                command = self.get_command()
            except EndOfFile:
                return commands
            else:
                commands.append(command)

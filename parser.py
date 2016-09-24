import logging

from common import Token
from expander import parse_replacement_text
from fonts import FontRange
from common_parsing import pg as common_pg
from parse_utils import (ExpectedParsingError, ExhaustedTokensError,
                         is_end_token)
from general_text_parser import gen_txt_pg


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


pg = common_pg.copy_to_extend()


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
@pg.production('command : input')
@pg.production('command : END')
def command(p):
    return p[0]


@pg.production('write : IMMEDIATE write')
def immediate_write(p):
    p[1].value['prefix'] = 'immediate'
    return p[1]


@pg.production('write : WRITE number general_text')
def write(p):
    # TODO: Implement.
    return Token(type_='write',
                 value={'stream_number': p[1], 'content': p[2], 'prefix': None})


@pg.production('message : ERROR_MESSAGE general_text')
@pg.production('message : MESSAGE general_text')
def message(p):
    # TODO: Implement.
    return Token(type_='message',
                 value={'content': p[1]})


pg.add_recent_productions(gen_txt_pg)


@pg.production('assignment : macro_assignment')
@pg.production('assignment : non_macro_assignment')
def assignment(p):
    return p[0]


@pg.production('macro_assignment : prefix macro_assignment')
def macro_assignment_prefix(p):
    p[1].value['prefixes'].add(p[0])
    return p[1]


@pg.production('prefix : GLOBAL')
@pg.production('prefix : LONG')
@pg.production('prefix : OUTER')
def prefix(p):
    return p[0].type


@pg.production('macro_assignment : definition')
def macro_assignment(p):
    macro_token = Token(type_='macro_assignment',
                        value={'prefixes': set(),
                               'definition': p[0]})
    return macro_token


@pg.production('definition : def control_sequence definition_text')
def definition(p):
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
def def_(p):
    return p[0]


@pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
def definition_text(p):
    # TODO: maybe move this parsing logic to inside the Expander.
    replacement_text = parse_replacement_text(p[2].value)
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': p[0].value,
                                  'replacement_text': replacement_text})
    return def_text_token


# End of 'macro assignment', an assignment.

# Start of 'simple assignment', an assignment. (Non macro is just this with
# an optional 'global' prefix.)


# TODO: I moved all the global prefixes inside each assignment, because I was
# implementing the commands in here. Now I am not, I can move them out again
# to up here.
@pg.production('non_macro_assignment : simple_assignment')
def non_macro_assignment(p):
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
def simple_assignment(p):
    return p[0]


@pg.production('simple_assignment : optional_globals FONT_DEF_TOKEN')
def simple_assignment_font_selection(p):
    return Token(type_='font_selection',
                 value={'global': p[0], 'font_id': p[1].value})


# Start of 'variable assignment', a simple assignment.

@pg.production('simple_assignment : optional_globals variable_assignment')
def simple_assignment_variable(p):
    return p[0]


@pg.production('variable_assignment : optional_globals partial_variable_assignment')
def variable_assignment(p):
    is_global = p[0]
    variable, value = p[1]
    return Token(type_='variable_assignment',
                 value={'global': is_global,
                        'variable': variable, 'value': value})


@pg.production('partial_variable_assignment : token_variable equals general_text')
@pg.production('partial_variable_assignment : token_variable equals filler token_variable')
def partial_variable_assignment_token_variable(p):
    value = Token(type_='token_list', value=p[-1])
    return [p[0], value]


@pg.production('partial_variable_assignment : mu_glue_variable equals mu_glue')
@pg.production('partial_variable_assignment : glue_variable equals glue')
@pg.production('partial_variable_assignment : dimen_variable equals dimen')
@pg.production('partial_variable_assignment : integer_variable equals number')
def partial_variable_assignment_quantity(p):
    return [p[0], p[2]]


# End of 'variable assignment', a simple assignment.

# Start of 'arithmetic', a simple assignment.


@pg.production('arithmetic : optional_globals ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(p):
    # TODO: Allow arithmetic on parameters.
    # TODO: Allow multiply and divide operations.
    # TODO: Allow arithmetic on dimen, glue and muglue.
    return Token(type_='advance',
                 value={'global': p[0], 'variable': p[2], 'value': p[4]})


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(p):
    return None


# End of 'arithmetic', a simple assignment.

# Start of 'code assignment', a simple assignment.


@pg.production('code_assignment : optional_globals code_name number equals number')
def code_assignment(p):
    return Token(type_='code_assignment',
                 value={'global': p[0], 'code_type': p[1],
                        'char': p[2], 'code': p[4]})


@pg.production('code_name : CAT_CODE')
@pg.production('code_name : MATH_CODE')
@pg.production('code_name : UPPER_CASE_CODE')
@pg.production('code_name : LOWER_CASE_CODE')
@pg.production('code_name : SPACE_FACTOR_CODE')
@pg.production('code_name : DELIMITER_CODE')
def code_name_cat(p):
    return p[0].type


# End of 'code assignment', a simple assignment.

# Start of 'let assignment', a simple assignment.


@pg.production('let_assignment : optional_globals LET control_sequence equals one_optional_space UNEXPANDED_TOKEN')
def let_assignment_control_sequence(p):
    is_global = p[0]
    target_token = p[5].value
    new_name = p[2].value['name']
    return Token(type_='let_assignment',
                 value={'global': is_global, 'name': new_name,
                        'target_token': target_token})


# End of 'let assignment', a simple assignment.

# Start of 'short-hand definition', a simple assignment.


@pg.production('short_hand_definition : optional_globals short_hand_def control_sequence equals number')
def short_hand_definition(p):
    is_global = p[0]
    code = p[4]
    def_type = p[1].type
    control_sequence_name = p[2].value['name']
    return Token(type_='short_hand_definition',
                 value={'global': is_global,
                        'code': code,
                        'def_type': def_type,
                        'control_sequence_name': control_sequence_name})


@pg.production('short_hand_def : CHAR_DEF')
@pg.production('short_hand_def : MATH_CHAR_DEF')
@pg.production('short_hand_def : COUNT_DEF')
@pg.production('short_hand_def : DIMEN_DEF')
@pg.production('short_hand_def : SKIP_DEF')
@pg.production('short_hand_def : MU_SKIP_DEF')
@pg.production('short_hand_def : TOKS_DEF')
def short_hand_def(p):
    return p[0]


# End of 'short-hand definition', a simple assignment.

# Start of 'family assignment', a simple assignment.


@pg.production('family_assignment : optional_globals family_member equals font')
def family_assignment(p):
    is_global = p[0]
    # TODO: will this work for productions of font other than FONT_DEF_TOKEN?
    font_id = p[3].value
    font_range = p[1].type
    family_nr = p[1].value
    return Token(type_='family_assignment',
                 value={'global': is_global,
                        'family_nr': family_nr,
                        'font_range': font_range,
                        'font_id': font_id})


@pg.production('family_member : font_range number')
def family_member(p):
    return Token(type_=p[0], value=p[1])


@pg.production('font_range : TEXT_FONT')
@pg.production('font_range : SCRIPT_FONT')
@pg.production('font_range : SCRIPT_SCRIPT_FONT')
def font_range(p):
    return FontRange(p[0].type)


# End of 'family assignment', a simple assignment.

# Start of 'set box assignment', a simple assignment.


@pg.production('set_box_assignment : optional_globals SET_BOX number equals filler box')
def set_box_assignment(p):
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
def box(p):
    return Token(type_='h_box', value={'specification': p[1],
                                       'contents': p[3]})


@pg.production('box_specification : to dimen filler')
def box_specification_to(p):
    return Token(type_='to', value=p[1])


@pg.production('box_specification : spread dimen filler')
def box_specification_spread(p):
    return Token(type_='spread', value=p[1])


@pg.production('box_specification : filler')
def box_specification_empty(p):
    return None


# End of 'set box assignment', a simple assignment.

# Start of 'font definition', a simple assignment.


# TODO: all these global things can be done *much* better now, because the
# action is taken *after* all the parsing is done. That is great.
@pg.production('font_definition : optional_globals FONT control_sequence equals optional_spaces file_name filler at_clause')
def font_definition(p):
    is_global = p[0]
    file_name, at_clause = p[5], p[7]
    control_sequence_name = p[2].value['name']
    return Token(type_='font_definition',
                 value={'global': is_global, 'file_name': file_name,
                        'at_clause': at_clause,
                        'control_sequence_name': control_sequence_name})


@pg.production('at_clause : at dimen')
def at_clause_dimen(p):
    return Token(type_='at_dimen', value=p[1])


@pg.production('at_clause : scaled number')
def at_clause_scaled(p):
    return Token(type_='scaled_number', value=p[1])


@pg.production('at_clause : optional_spaces')
def at_clause_empty(p):
    return None


# End of 'font definition', a simple assignment.

# Start of 'global assignment', a simple assignment.


@pg.production('global_assignment : optional_globals global_assignment')
def global_assignment(p):
    # Global prefixes have no effect.
    return p[1]


@pg.production('global_assignment : font_assignment')
@pg.production('global_assignment : hyphenation_assignment')
# @pg.production('global_assignment : box_size_assignment')
# @pg.production('global_assignment : interaction_mode_assignment')
# @pg.production('global_assignment : intimate_assignment')
def global_assignment(p):
    return p[0]


@pg.production('font_assignment : SKEW_CHAR font equals number')
@pg.production('font_assignment : HYPHEN_CHAR font equals number')
def font_assignment(p):
    # TODO: as for font definition, does this work for non-FONT_DEF_TOKEN font
    # productions?
    font_id = p[1].value
    type_ = '{}_assignment'.format(p[0].type.lower())
    return Token(type_=type_,
                 value={'font_id': font_id, 'code': p[3]})


@pg.production('font : FONT_DEF_TOKEN')
# @pg.production('font : family_member')
# @pg.production('font : FONT')
def font(p):
    return p[0]


@pg.production('hyphenation_assignment : HYPHENATION general_text')
@pg.production('hyphenation_assignment : PATTERNS general_text')
def hyphenation_assignment(p):
    # TODO: Implement.
    return Token(type_=p[0],
                 value=p[1])


# End of 'global assignment', a simple assignment.


@pg.production('optional_globals : optional_globals GLOBAL')
def optional_globals_extend(p):
    return True


@pg.production('optional_globals : GLOBAL')
@pg.production('optional_globals : empty')
def optional_globals(p):
    return bool(p[0])


# End of the simple assignments.


@pg.production('add_kern : KERN dimen')
@pg.production('add_kern : MATH_KERN mu_dimen')
def add_kern(p):
    # TODO: Implement.
    return Token(type_=p[0].type, value=p[1])


@pg.production('add_glue : H_FIL')
@pg.production('add_glue : H_FILL')
@pg.production('add_glue : H_STRETCH_OR_SHRINK')
@pg.production('add_glue : H_FIL_NEG')
@pg.production('add_glue : V_FIL')
@pg.production('add_glue : V_FILL')
@pg.production('add_glue : V_STRETCH_OR_SHRINK')
@pg.production('add_glue : V_FIL_NEG')
def add_special_glue(p):
    # TODO: Implement.
    return Token(type_=p[0], value=None)


@pg.production('add_glue : H_SKIP glue')
@pg.production('add_glue : V_SKIP glue')
def add_glue(p):
    # TODO: Implement.
    return Token(type_=p[0], value=p[1])


@pg.production('vertical_rule : V_RULE rule_specification')
@pg.production('horizontal_rule : H_RULE rule_specification')
def rule(p):
    # TODO: Implement.
    return Token(type_=p[0], value=p[1])


@pg.production('rule_specification : rule_dimension rule_specification')
def rule_specification(p):
    t = p[1]
    # TODO: does this give the correct overwrite order?
    # Presumably, repeating the same axis should obey the last one.
    dim_type = p[0].value['axis']
    t.value[dim_type] = p[0].value['dimen']
    return t


@pg.production('rule_specification : optional_spaces')
def rule_specification_empty(p):
    dims = {'width': None, 'height': None, 'depth': None}
    return Token(type_='rule_specification', value=dims)


# TODO: these literals are getting unclear. Introduce some convention to make
# clear which (non-terminal) tokens represent literals.
@pg.production('rule_dimension : width dimen')
@pg.production('rule_dimension : height dimen')
@pg.production('rule_dimension : depth dimen')
def rule_dimension(p):
    return Token(type_='rule_dimension',
                 value={'axis': p[0], 'dimen': p[1]})


@pg.production('input : INPUT file_name')
def input_file(p):
    return Token(type_='input',
                 value={'file_name': p[1]})


@pg.production('file_name : character')
@pg.production('file_name : file_name character')
def file_name(p):
    if len(p) > 1:
        return p[0] + p[1].value['char']
    else:
        return p[0].value['char']


@pg.error
def error(look_ahead):
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

# Build the parser
parser = pg.build()

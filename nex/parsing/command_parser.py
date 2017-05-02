import logging

from ..tokens import BuiltToken
from ..expander import parse_replacement_text
from ..fonts import FontRange
from .common_parsing import pg as common_pg
from .utils import (ExpectedParsingError, ExhaustedTokensError,
                    is_end_token)
from .general_text_parser import gen_txt_pg


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
@pg.production('command : un_box')
@pg.production('command : vertical_rule')
@pg.production('command : horizontal_rule')
@pg.production('command : input')
@pg.production('command : RIGHT_BRACE')
@pg.production('command : LEFT_BRACE')
@pg.production('command : END')
@pg.production('command : char')
@pg.production('command : CHAR_DEF_TOKEN')
@pg.production('command : INDENT')
def command(p):
    return p[0]


@pg.production('write : IMMEDIATE write')
def immediate_write(p):
    p[1].value['prefix'] = 'immediate'
    return p[1]


@pg.production('write : WRITE number general_text')
def write(p):
    # TODO: Implement.
    return BuiltToken(type_='write',
                      value={'stream_number': p[1], 'content': p[2],
                             'prefix': None},
                      position_like=p)


@pg.production('message : ERROR_MESSAGE general_text')
@pg.production('message : MESSAGE general_text')
def message(p):
    # TODO: Implement.
    return BuiltToken(type_='message',
                      value={'content': p[1]},
                      position_like=p)


pg.add_recent_productions(gen_txt_pg)


# Start of 'assignment', a command. This is a big section.


@pg.production('assignment : macro_assignment')
@pg.production('assignment : non_macro_assignment')
def assignment(p):
    return p[0]


# Start of 'macro assignment', an assignment.


@pg.production('macro_assignment : prefix macro_assignment')
def macro_assignment_prefix(p):
    p[1].value['prefixes'].add(p[0])
    return p[1]


@pg.production('prefix : GLOBAL_MOD')
@pg.production('prefix : LONG_MOD')
@pg.production('prefix : OUTER_MOD')
def prefix(p):
    return p[0].type


@pg.production('macro_assignment : definition')
def macro_assignment(p):
    macro_token = BuiltToken(type_='macro_assignment',
                             value={'prefixes': set(),
                                    'definition': p[0]},
                             position_like=p)
    return macro_token


@pg.production('definition : def control_sequence definition_text')
def definition(p):
    def_token = BuiltToken(type_='definition',
                           value={'def_type': p[0],
                                  'name': p[1].value['name'],
                                  'text': p[2]},
                           position_like=p)
    return def_token


# TODO: can automate this, and many like it, using expander maps.
@pg.production('def : DEF_')
@pg.production('def : G_DEF')
@pg.production('def : E_DEF')
@pg.production('def : X_DEF')
def def_(p):
    return p[0]


@pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
def definition_text(p):
    # TODO: maybe move this parsing logic to inside the Expander.
    replacement_text = parse_replacement_text(p[2].value)
    def_text_token = BuiltToken(type_='definition_text',
                                value={'parameter_text': p[0].value,
                                       'replacement_text': replacement_text},
                                position_like=p)
    return def_text_token


# End of 'macro assignment', an assignment.

# Start of 'non-macro assignment', an assignment.
# (This is basically just 'simple assignment's, with an optional \global
# prefix.)


@pg.production('non_macro_assignment : GLOBAL_MOD non_macro_assignment')
def non_macro_assignment_global(p):
    tok = p[1]
    tok.value['global'] = True
    return tok


@pg.production('non_macro_assignment : simple_assignment')
def non_macro_assignment(p):
    tok = p[0]
    # A simple assignment is local (non-global) unless indicated otherwise.
    # The only way to be already global is if the simple assigment is of type
    # 'global assignment'. In this case, we should not touch the value.
    if 'global' not in tok.value:
        tok.value['global'] = False
    return tok


@pg.production('simple_assignment : variable_assignment')
@pg.production('simple_assignment : arithmetic')
@pg.production('simple_assignment : code_assignment')
@pg.production('simple_assignment : let_assignment')
@pg.production('simple_assignment : short_hand_definition')
@pg.production('simple_assignment : font_selection')
@pg.production('simple_assignment : family_assignment')
@pg.production('simple_assignment : set_box_assignment')
@pg.production('simple_assignment : font_definition')
@pg.production('simple_assignment : global_assignment')
def simple_assignment(p):
    return p[0]


# 'font selection', a simple assignment.


@pg.production('font_selection : FONT_DEF_TOKEN')
def simple_assignment_font_selection(p):
    return BuiltToken(type_='font_selection',
                      value={'font_id': p[0].value},
                      position_like=p)


# Start of 'variable assignment', a simple assignment.

@pg.production('variable_assignment : partial_variable_assignment')
def variable_assignment(p):
    variable, value = p[0]
    return BuiltToken(type_='variable_assignment',
                      value={'variable': variable, 'value': value},
                      position_like=p[0])


@pg.production('partial_variable_assignment : token_variable equals general_text')
@pg.production('partial_variable_assignment : token_variable equals filler token_variable')
def partial_variable_assignment_token_variable(p):
    value = BuiltToken(type_='token_list', value=p[-1],
                       position_like=p)
    return [p[0], value]


@pg.production('partial_variable_assignment : mu_glue_variable equals mu_glue')
@pg.production('partial_variable_assignment : glue_variable equals glue')
@pg.production('partial_variable_assignment : dimen_variable equals dimen')
@pg.production('partial_variable_assignment : integer_variable equals number')
def partial_variable_assignment_quantity(p):
    return [p[0], p[2]]


# End of 'variable assignment', a simple assignment.

# Start of 'arithmetic', a simple assignment.


@pg.production('arithmetic : ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(p):
    # TODO: Allow arithmetic on parameters.
    # TODO: Allow multiply and divide operations.
    # TODO: Allow arithmetic on dimen, glue and muglue.
    return BuiltToken(type_='advance',
                      value={'variable': p[1], 'value': p[3]},
                      position_like=p)


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(p):
    return None


# End of 'arithmetic', a simple assignment.

# Start of 'code assignment', a simple assignment.


@pg.production('code_assignment : code_name number equals number')
def code_assignment(p):
    return BuiltToken(type_='code_assignment',
                      value={'code_type': p[0].type, 'char': p[1], 'code': p[3]},
                      position_like=p)


@pg.production('code_name : CAT_CODE')
@pg.production('code_name : MATH_CODE')
@pg.production('code_name : UPPER_CASE_CODE')
@pg.production('code_name : LOWER_CASE_CODE')
@pg.production('code_name : SPACE_FACTOR_CODE')
@pg.production('code_name : DELIMITER_CODE')
def code_name(p):
    return p[0]


# End of 'code assignment', a simple assignment.

# Start of 'let assignment', a simple assignment.


@pg.production('let_assignment : LET control_sequence equals one_optional_space LET_TARGET')
def let_assignment_control_sequence(p):
    target_token = p[4].value
    new_name = p[1].value['name']
    return BuiltToken(type_='let_assignment',
                      value={'name': new_name, 'target_token': target_token},
                      position_like=p)


# End of 'let assignment', a simple assignment.

# Start of 'short-hand definition', a simple assignment.


@pg.production('short_hand_definition : short_hand_def control_sequence equals number')
def short_hand_definition(p):
    code = p[3]
    def_type = p[0].type
    control_sequence_name = p[1].value['name']
    return BuiltToken(type_='short_hand_definition',
                      value={'code': code, 'def_type': def_type,
                             'control_sequence_name': control_sequence_name},
                      position_like=p)


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


@pg.production('family_assignment : family_member equals font')
def family_assignment(p):
    # TODO: will this work for productions of font other than FONT_DEF_TOKEN?
    font_id = p[2].value
    font_range = p[0].type
    family_nr = p[0].value
    return BuiltToken(type_='family_assignment',
                      value={'family_nr': family_nr, 'font_range': font_range,
                             'font_id': font_id},
                      position_like=p)


@pg.production('family_member : font_range number')
def family_member(p):
    return BuiltToken(type_=p[0].value, value=p[1],
                      position_like=p)


@pg.production('font_range : TEXT_FONT')
@pg.production('font_range : SCRIPT_FONT')
@pg.production('font_range : SCRIPT_SCRIPT_FONT')
def font_range(p):
    return BuiltToken(type_='font_range',
                      value=FontRange(p[0].type),
                      position_like=p)


# End of 'family assignment', a simple assignment.

# Start of 'set box assignment', a simple assignment.


@pg.production('set_box_assignment : SET_BOX number equals filler box')
def set_box_assignment(p):
    return BuiltToken(type_='set_box_assignment',
                      value={'nr': p[1], 'contents': p[4]},
                      position_like=p)


# @pg.production('box : BOX number')
# @pg.production('box : COPY number')
# @pg.production('box : LAST_BOX')
# @pg.production('box : V_SPLIT number to dimen')
@pg.production('box : H_BOX box_specification LEFT_BRACE HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE')
# @pg.production('box : V_BOX box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
# @pg.production('box : V_TOP box_specification LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
def box(p):
    return BuiltToken(type_='h_box',
                      value={'specification': p[1], 'contents': p[3]},
                      position_like=p)


@pg.production('box_specification : to dimen filler')
def box_specification_to(p):
    return BuiltToken(type_='to', value=p[1],
                      position_like=p)


@pg.production('box_specification : spread dimen filler')
def box_specification_spread(p):
    return BuiltToken(type_='spread', value=p[1],
                      position_like=p)


@pg.production('box_specification : filler')
def box_specification_empty(p):
    return None


# End of 'set box assignment', a simple assignment.

# Start of 'font definition', a simple assignment.


@pg.production('font_definition : FONT control_sequence equals optional_spaces file_name filler at_clause')
def font_definition(p):
    control_sequence_name = p[1].value['name']
    return BuiltToken(type_='font_definition',
                      value={'file_name': p[4], 'at_clause': p[6],
                             'control_sequence_name': control_sequence_name},
                      position_like=p)


@pg.production('at_clause : at dimen')
def at_clause_dimen(p):
    return BuiltToken(type_='at_dimen', value=p[1],
                      position_like=p)


@pg.production('at_clause : scaled number')
def at_clause_scaled(p):
    return BuiltToken(type_='scaled_number', value=p[1],
                      position_like=p)


@pg.production('at_clause : optional_spaces')
def at_clause_empty(p):
    return None


# End of 'font definition', a simple assignment.

# Start of 'global assignment', a simple assignment.


@pg.production('global_assignment : font_assignment')
@pg.production('global_assignment : hyphenation_assignment')
# @pg.production('global_assignment : box_size_assignment')
# @pg.production('global_assignment : interaction_mode_assignment')
# @pg.production('global_assignment : intimate_assignment')
def global_assignment(p):
    tok = p[0]
    # Global assignments are always global, even without the \global prefix.
    tok.value['global'] = True
    return tok


@pg.production('font_assignment : SKEW_CHAR font equals number')
@pg.production('font_assignment : HYPHEN_CHAR font equals number')
def font_assignment(p):
    # TODO: as for font definition, does this work for non-FONT_DEF_TOKEN font
    # productions?
    font_id = p[1].value
    type_ = '{}_assignment'.format(p[0].type.lower())
    return BuiltToken(type_=type_,
                      value={'font_id': font_id, 'code': p[3]},
                      position_like=p)


@pg.production('font : FONT_DEF_TOKEN')
# @pg.production('font : family_member')
# @pg.production('font : FONT')
def font(p):
    return p[0]


@pg.production('hyphenation_assignment : HYPHENATION general_text')
@pg.production('hyphenation_assignment : PATTERNS general_text')
def hyphenation_assignment(p):
    return BuiltToken(type_=p[0].type, value={'content': p[1]},
                      position_like=p)


# End of 'global assignment', a simple assignment.


# End of 'simple assignment', an assignment.


# End of 'assignment', a command.


@pg.production('add_kern : KERN dimen')
@pg.production('add_kern : MATH_KERN mu_dimen')
def add_kern(p):
    # TODO: Implement.
    return BuiltToken(type_=p[0].type, value=p[1],
                      position_like=p)


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
    return BuiltToken(type_=p[0].type, value=None,
                      position_like=p)


@pg.production('add_glue : H_SKIP glue')
@pg.production('add_glue : V_SKIP glue')
def add_glue(p):
    # TODO: Implement.
    return BuiltToken(type_=p[0].type, value=p[1],
                      position_like=p)


@pg.production('vertical_rule : V_RULE rule_specification')
@pg.production('horizontal_rule : H_RULE rule_specification')
def rule(p):
    # TODO: Implement.
    return BuiltToken(type_=p[0].type, value=p[1].value,
                      position_like=p)


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
    return BuiltToken(type_='rule_specification', value=dims,
                      position_like=p)


# TODO: these literals are getting unclear. Introduce some convention to make
# clear which (non-terminal) tokens represent literals.
@pg.production('rule_dimension : width dimen')
@pg.production('rule_dimension : height dimen')
@pg.production('rule_dimension : depth dimen')
def rule_dimension(p):
    print(p[0])
    return BuiltToken(type_='rule_dimension',
                      value={'axis': p[0].value, 'dimen': p[1]},
                      position_like=p)


@pg.production('input : INPUT file_name')
def input_file(p):
    return BuiltToken(type_='input',
                      value={'file_name': p[1].value},
                      position_like=p)


@pg.production('file_name : character')
@pg.production('file_name : file_name character')
def file_name(p):
    if len(p) > 1:
        s = p[0].value + p[1].value['char']
    else:
        s = p[0].value['char']
    return BuiltToken(type_='file_name',
                      value=s,
                      position_like=p)


@pg.production('char : CHAR number')
def char(p):
    return BuiltToken(type_='char',
                      value={'code': p[1]},
                      position_like=p)


# TODO: I wonder if I could make a decorator to make a token of the correct
# type based on the production rule. Then I just have to return a dict.
@pg.production('un_box : un_box_type number')
def un_box(p):
    un_box_type = p[0].type.lower()
    return BuiltToken(type_=un_box_type,
                      value={'nr': p[1]},
                      position_like=p)


@pg.production('un_box_type : UN_H_BOX')
@pg.production('un_box_type : UN_H_COPY')
@pg.production('un_box_type : UN_V_BOX')
@pg.production('un_box_type : UN_V_COPY')
def un_box_type(p):
    return p[0]


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
command_parser = pg.build()

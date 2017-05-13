from enum import Enum
from datetime import datetime

from .tokens import InstructionToken
from .instructions import Instructions
from .registers import check_type
from .utils import NotInScopeError


params = {
    'PRE_TOLERANCE': Instructions.integer_parameter,
    'TOLERANCE': Instructions.integer_parameter,
    'H_BADNESS': Instructions.integer_parameter,
    'V_BADNESS': Instructions.integer_parameter,
    'LINE_PENALTY': Instructions.integer_parameter,
    'HYPHEN_PENALTY': Instructions.integer_parameter,
    'EX_HYPHEN_PENALTY': Instructions.integer_parameter,
    'BIN_OP_PENALTY': Instructions.integer_parameter,
    'REL_PENALTY': Instructions.integer_parameter,
    'CLUB_PENALTY': Instructions.integer_parameter,
    'WIDOW_PENALTY': Instructions.integer_parameter,
    'DISPLAY_WIDOW_PENALTY': Instructions.integer_parameter,
    'BROKEN_PENALTY': Instructions.integer_parameter,
    'PRE_DISPLAY_PENALTY': Instructions.integer_parameter,
    'POST_DISPLAY_PENALTY': Instructions.integer_parameter,
    'INTER_LINE_PENALTY': Instructions.integer_parameter,
    'FLOATING_PENALTY': Instructions.integer_parameter,
    'OUTPUT_PENALTY': Instructions.integer_parameter,
    'DOUBLE_HYPHEN_DEMERITS': Instructions.integer_parameter,
    'FINAL_HYPHEN_DEMERITS': Instructions.integer_parameter,
    'ADJ_DEMERITS': Instructions.integer_parameter,
    'LOOSENESS': Instructions.integer_parameter,
    'PAUSING': Instructions.integer_parameter,
    'HOLDING_INSERTS': Instructions.integer_parameter,
    'TRACING_ON_LINE': Instructions.integer_parameter,
    'TRACING_MACROS': Instructions.integer_parameter,
    'TRACING_STATS': Instructions.integer_parameter,
    'TRACING_PARAGRAPHS': Instructions.integer_parameter,
    'TRACING_PAGES': Instructions.integer_parameter,
    'TRACING_OUTPUT': Instructions.integer_parameter,
    'TRACING_LOSTCHARS': Instructions.integer_parameter,
    'TRACING_COMMANDS': Instructions.integer_parameter,
    'TRACING_RESTORES': Instructions.integer_parameter,
    'LANGUAGE': Instructions.integer_parameter,
    'UC_HYPH': Instructions.integer_parameter,
    'LEFT_HYPHEN_MIN': Instructions.integer_parameter,
    'RIGHT_HYPHEN_MIN': Instructions.integer_parameter,
    'GLOBAL_DEFS': Instructions.integer_parameter,
    'MAX_DEAD_CYCLES': Instructions.integer_parameter,
    'HANG_AFTER': Instructions.integer_parameter,
    'FAM': Instructions.integer_parameter,
    'MAG': Instructions.integer_parameter,
    'ESCAPE_CHAR': Instructions.integer_parameter,
    'DEFAULT_HYPHEN_CHAR': Instructions.integer_parameter,
    'DEFAULT_SKEW_CHAR': Instructions.integer_parameter,
    'END_LINE_CHAR': Instructions.integer_parameter,
    'NEW_LINE_CHAR': Instructions.integer_parameter,
    'DELIMITER_FACTOR': Instructions.integer_parameter,
    # THESE TIME ONES WILL BE SET IN GET_INITIAL_PARAMETERS.
    'TIME': Instructions.integer_parameter,
    'DAY': Instructions.integer_parameter,
    'MONTH': Instructions.integer_parameter,
    'YEAR': Instructions.integer_parameter,
    'SHOW_BOX_BREADTH': Instructions.integer_parameter,
    'SHOW_BOX_DEPTH': Instructions.integer_parameter,
    'ERROR_CONTEXT_LINES': Instructions.integer_parameter,
    'H_FUZZ': Instructions.dimen_parameter,
    'V_FUZZ': Instructions.dimen_parameter,
    'OVER_FULL_RULE': Instructions.dimen_parameter,
    'H_SIZE': Instructions.dimen_parameter,
    'V_SIZE': Instructions.dimen_parameter,
    'MAX_DEPTH': Instructions.dimen_parameter,
    'SPLIT_MAX_DEPTH': Instructions.dimen_parameter,
    'BOX_MAX_DEPTH': Instructions.dimen_parameter,
    'LINE_SKIP_LIMIT': Instructions.dimen_parameter,
    'DELIMITER_SHORT_FALL': Instructions.dimen_parameter,
    'NULL_DELIMITER_SPACE': Instructions.dimen_parameter,
    'SCRIPT_SPACE': Instructions.dimen_parameter,
    'MATH_SURROUND': Instructions.dimen_parameter,
    'PRE_DISPLAY_SIZE': Instructions.dimen_parameter,
    'DISPLAY_WIDTH': Instructions.dimen_parameter,
    'DISPLAY_INDENT': Instructions.dimen_parameter,
    'PAR_INDENT': Instructions.dimen_parameter,
    'HANG_INDENT': Instructions.dimen_parameter,
    'H_OFFSET': Instructions.dimen_parameter,
    'V_OFFSET': Instructions.dimen_parameter,
    'BASE_LINE_SKIP': Instructions.glue_parameter,
    'LINE_SKIP': Instructions.glue_parameter,
    'PAR_SKIP': Instructions.glue_parameter,
    'ABOVE_DISPLAY_SKIP': Instructions.glue_parameter,
    'ABOVE_DISPLAY_SHORT_SKIP': Instructions.glue_parameter,
    'BELOW_DISPLAY_SKIP': Instructions.glue_parameter,
    'BELOW_DISPLAY_SHORT_SKIP': Instructions.glue_parameter,
    'LEFT_SKIP': Instructions.glue_parameter,
    'RIGHT_SKIP': Instructions.glue_parameter,
    'TOP_SKIP': Instructions.glue_parameter,
    'SPLIT_TOP_SKIP': Instructions.glue_parameter,
    'TAB_SKIP': Instructions.glue_parameter,
    'SPACE_SKIP': Instructions.glue_parameter,
    'X_SPACE_SKIP': Instructions.glue_parameter,
    'PAR_FILL_SKIP': Instructions.glue_parameter,
    'THIN_MU_SKIP': Instructions.mu_glue_parameter,
    'MED_MU_SKIP': Instructions.mu_glue_parameter,
    'THICK_MU_SKIP': Instructions.mu_glue_parameter,
    'OUTPUT': Instructions.token_parameter,
    'EVERY_PAR': Instructions.token_parameter,
    'EVERY_MATH': Instructions.token_parameter,
    'EVERY_DISPLAY': Instructions.token_parameter,
    'EVERY_H_BOX': Instructions.token_parameter,
    'EVERY_V_BOX': Instructions.token_parameter,
    'EVERY_JOB': Instructions.token_parameter,
    'EVERY_CR': Instructions.token_parameter,
    'ERR_HELP': Instructions.token_parameter,
}
Parameters = Enum('Parameters', {s.lower(): s for s in params})
param_to_instr = {p: params[p.value] for p in Parameters}

param_instrs = (
    Instructions.integer_parameter,
    Instructions.dimen_parameter,
    Instructions.glue_parameter,
    Instructions.mu_glue_parameter,
    Instructions.token_parameter,
)
parameter_instr_types = tuple(i.value for i in param_instrs)

glue_keys = ('dimen', 'stretch', 'shrink')


def is_parameter_type(type_):
    return type_ in parameter_instr_types


def get_initial_parameters():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    minutes_since_midnight = int(seconds_since_midnight // 60)

    def param_instr_subset(instr):
        return filter(lambda p: param_to_instr[p] == instr, Parameters)

    parameter_values = {}

    integer_parameters = param_instr_subset(Instructions.integer_parameter)
    for p in integer_parameters:
        parameter_values[p] = 0
    parameter_values[Parameters.tolerance] = 10000
    parameter_values[Parameters.max_dead_cycles] = 25
    parameter_values[Parameters.hang_after] = 1
    parameter_values[Parameters.mag] = 1000
    parameter_values[Parameters.escape_char] = ord('\\')
    parameter_values[Parameters.end_line_char] = ord('\r')
    # These time ones will be set in get_initial_parameters.
    parameter_values[Parameters.time] = minutes_since_midnight
    parameter_values[Parameters.day] = now.day
    parameter_values[Parameters.month] = now.month
    parameter_values[Parameters.year] = now.year

    dimen_parameters = param_instr_subset(Instructions.dimen_parameter)
    for p in dimen_parameters:
        parameter_values[p] = 0

    def get_zero_glue():
        return {k: 0 for k in glue_keys}
    glue_parameters = param_instr_subset(Instructions.glue_parameter)
    for p in glue_parameters:
        parameter_values[p] = get_zero_glue()

    mu_glue_parameters = param_instr_subset(Instructions.mu_glue_parameter)
    for p in mu_glue_parameters:
        parameter_values[p] = get_zero_glue()

    def get_empty_token_list():
        return InstructionToken(
            Instructions.balanced_text_and_right_brace,
            value=[],
            line_nr='abstract',
        )
    token_parameters = param_instr_subset(Instructions.token_parameter)
    for p in token_parameters:
        parameter_values[p] = get_empty_token_list()

    return TexParameterValues(parameter_values)


def get_local_parameters(enclosing_scope):
    return TexParameterValues({})


class TexParameterValues:

    def __init__(self, parameter_value_map):
        self.parameter_values = parameter_value_map

    def get(self, parameter):
        try:
            return self.parameter_values[parameter]
        # TODO: Distinguish KeyErrors caused by key not making any sense, from
        # KeyErrors caused by value not being defined in this scope.
        except KeyError:
            raise NotInScopeError

    def set(self, parameter, value):
        # TODO: Initialize all sensible keys, pointing to 'None' for local
        # scopes. Only allow setting keys that already exist, and
        # raise a NotInScopeError if None is returned.
        # Will avoid having to lookup from this global dict.
        parameter_instr = param_to_instr[parameter]
        parameter_type = parameter_instr.value
        check_type(parameter_type, value)
        self.parameter_values[parameter] = value

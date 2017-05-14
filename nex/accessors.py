from enum import Enum
from datetime import datetime

from .tokens import InstructionToken, instructions_to_types
from .instructions import Instructions, register_instructions
from .utils import NotInScopeError


def check_type(type_, value):
    # TODO: Make type checking more strict, and do in more places.
    if type_ in (Instructions.count.value,
                 Instructions.dimen.value,
                 Instructions.integer_parameter.value,
                 Instructions.dimen_parameter.value):
        expected_type = int
    elif type_ in (Instructions.skip.value,
                   Instructions.mu_skip.value,
                   Instructions.glue_parameter.value,
                   Instructions.mu_glue_parameter.value):
        expected_type = dict
    elif type_ in (Instructions.toks.value,
                   Instructions.token_parameter.value):
        expected_type = list
    if not isinstance(value, expected_type):
        raise TypeError('Value has wrong type')


class TexNamedValues:
    """
    Accessor for either parameters or special values.
    names_to_values: A container mapping names to values.
    names_to_types: A container mapping these names to their types.
    """

    def __init__(self, names_to_values, names_to_types):
        self.names_to_values = names_to_values
        self.names_to_types = names_to_types

    def _check_and_get_value(self, name):
        if name not in self.names_to_values:
            raise KeyError(f'Named value "{name}" does not exist')
        return self.names_to_values[name]

    def get(self, name):
        value = self._check_and_get_value(name)
        if value is None:
            raise NotInScopeError
        return value

    def set(self, name, value):
        self._check_and_get_value(name)
        value_type = self.names_to_types[name]
        check_type(value_type, value)
        self.names_to_values[name] = value


# Start of parameters.

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
param_to_type = {p: instr.value for p, instr in param_to_instr.items()}

param_instrs = (
    Instructions.integer_parameter,
    Instructions.dimen_parameter,
    Instructions.glue_parameter,
    Instructions.mu_glue_parameter,
    Instructions.token_parameter,
)
parameter_instr_types = instructions_to_types(param_instrs)

glue_keys = ('dimen', 'stretch', 'shrink')


def is_parameter_type(type_):
    return type_ in parameter_instr_types


def param_instr_subset(instr):
    return filter(lambda p: param_to_instr[p] == instr, Parameters)


integer_parameters = param_instr_subset(Instructions.integer_parameter)
dimen_parameters = param_instr_subset(Instructions.dimen_parameter)
glue_parameters = param_instr_subset(Instructions.glue_parameter)
mu_glue_parameters = param_instr_subset(Instructions.mu_glue_parameter)
token_parameters = param_instr_subset(Instructions.token_parameter)


def get_initial_parameters():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    minutes_since_midnight = int(seconds_since_midnight // 60)

    parameter_values = {}

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

    for p in dimen_parameters:
        parameter_values[p] = 0

    def get_zero_glue():
        return {k: 0 for k in glue_keys}
    for p in glue_parameters:
        parameter_values[p] = get_zero_glue()

    for p in mu_glue_parameters:
        parameter_values[p] = get_zero_glue()

    def get_empty_token_list():
        return InstructionToken(
            Instructions.balanced_text_and_right_brace,
            value=[],
            line_nr='abstract',
        )
    for p in token_parameters:
        parameter_values[p] = get_empty_token_list()

    return TexNamedValues(parameter_values, param_to_type)


def get_local_parameters(enclosing_scope):
    parameter_values = {p: None for p in Parameters}
    return TexNamedValues(parameter_values, param_to_type)


# End of parameters.

# Start of specials.

specials = {
    'SPACE_FACTOR': Instructions.special_integer,
    'PREV_GRAF': Instructions.special_integer,
    'DEAD_CYCLES': Instructions.special_integer,
    'INSERT_PENALTIES': Instructions.special_integer,

    'PREV_DEPTH': Instructions.special_dimen,
    'PAGE_GOAL': Instructions.special_dimen,
    'PAGE_TOTAL': Instructions.special_dimen,
    'PAGE_STRETCH': Instructions.special_dimen,
    'PAGE_FIL_STRETCH': Instructions.special_dimen,
    'PAGE_FILL_STRETCH': Instructions.special_dimen,
    'PAGE_FILLL_STRETCH': Instructions.special_dimen,
    'PAGE_SHRINK': Instructions.special_dimen,
    'PAGE_DEPTH': Instructions.special_dimen,
}
Specials = Enum('Specials', {s.lower(): s for s in specials})
special_to_instr = {p: specials[p.value] for p in Specials}
special_to_type = {p: instr.value for p, instr in special_to_instr.items()}

special_instrs = (
    Instructions.special_integer,
    Instructions.special_dimen,
)
special_instr_types = instructions_to_types(special_instrs)


def is_special_type(type_):
    return type_ in special_instr_types


def get_specials():
    return TexNamedValues(special_values, special_to_type)

# End of specials.

# Start of registers.


short_hand_reg_def_token_type_to_reg_type = {
    Instructions.count_def_token.value: Instructions.count.value,
    Instructions.dimen_def_token.value: Instructions.dimen.value,
    Instructions.skip_def_token.value: Instructions.skip.value,
    Instructions.mu_skip_def_token.value: Instructions.mu_skip.value,
    Instructions.toks_def_token.value: Instructions.toks.value,
}


register_types = instructions_to_types(register_instructions)


def is_register_type(type_):
    return type_ in register_types


class Registers:

    def __init__(self, register_map):
        # Map of strings representing register types, to a map of keys to
        # values.
        self.register_map = register_map

    def _check_and_get_register(self, type_):
        if type_ not in self.register_map:
            raise ValueError(f'No register of type {type_}')
        return self.register_map[type_]

    def _check_and_get_register_value(self, type_, i):
        register = self._check_and_get_register(type_)
        # Check address exists in register. This should not depend on anything
        # to do with scopes.
        if i not in register:
            raise ValueError(f'No register number {i} of type {type_}')
        return register[i]

    def get(self, type_, i):
        value = self._check_and_get_register_value(type_, i)
        if value is None:
            raise NotInScopeError('No value in register number {i} of type {type_}')
        return value

    def set(self, type_, i, value):
        # Check value matches what register is meant to hold.
        check_type(type_, value)
        # Check key already exists.
        self._check_and_get_register_value(type_, i)
        register = self._check_and_get_register(type_)
        register[i] = value


# TODO: Make these and similar into classmethods.
def get_initial_registers():
    def init_register():
        return {i: None for i in range(256)}
    register_map = {
        Instructions.count.value: init_register(),
        Instructions.dimen.value: init_register(),
        Instructions.skip.value: init_register(),
        Instructions.mu_skip.value: init_register(),
        Instructions.toks.value: init_register(),
    }
    return Registers(register_map)


def get_local_registers(enclosing_scope):
    return get_initial_registers()

# End of registers.

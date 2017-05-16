from datetime import datetime

from .tokens import InstructionToken, instructions_to_types
from .instructions import Instructions, register_instructions
from .parameters import (Parameters, Specials,
                         param_to_type, special_to_type,
                         param_instr_subset)
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

glue_keys = ('dimen', 'stretch', 'shrink')


class ParametersAccessor(TexNamedValues):

    @classmethod
    def default_initial(cls):
        # WARNING: If you think these variables might be useful in global
        # scope, beware. They are 'filter' objects, so they will only generate
        # their values once. If you want to use them repeatedly, cast them to a
        # suitable type. Otherwise they might break your tests in a way that is
        # not funny at all.
        integer_parameters = param_instr_subset(Instructions.integer_parameter)
        dimen_parameters = param_instr_subset(Instructions.dimen_parameter)
        glue_parameters = param_instr_subset(Instructions.glue_parameter)
        mu_glue_parameters = param_instr_subset(Instructions.mu_glue_parameter)
        token_parameters = param_instr_subset(Instructions.token_parameter)

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

        return cls(parameter_values, param_to_type)

    @classmethod
    def default_local(cls, enclosing_scope):
        parameter_values = {p: None for p in Parameters}
        return cls(parameter_values, param_to_type)


# End of parameters.

# Start of specials.

class SpecialsAccessor(TexNamedValues):

    @classmethod
    def from_defaults(cls):
        special_values = {s: None for s in Specials}
        # Guesses.
        special_values[Specials.space_factor] = 1000
        special_values[Specials.prev_graf] = 0
        special_values[Specials.dead_cycles] = 0
        special_values[Specials.insert_penalties] = 0
        special_values[Specials.page_total] = 0
        return cls(special_values, special_to_type)


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

    @classmethod
    def default_initial(cls):
        def init_register():
            return {i: None for i in range(256)}
        register_map = {
            Instructions.count.value: init_register(),
            Instructions.dimen.value: init_register(),
            Instructions.skip.value: init_register(),
            Instructions.mu_skip.value: init_register(),
            Instructions.toks.value: init_register(),
        }
        return cls(register_map)

    @classmethod
    def default_local(cls, enclosing_scope):
        return cls.default_initial()

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


# End of registers.

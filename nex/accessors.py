from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from datetime import datetime

from .tokens import InstructionToken, instructions_to_types
from .instructions import Instructions, register_instructions
from .box import AbstractBox
from .parameters import (Parameters, Specials,
                         param_to_type, special_to_type,
                         param_instr_subset)
from .codes import (CatCode, WeirdChar, MathClass, MathCode, GlyphCode,
                    DelimiterCode,
                    not_a_delimiter_code, ignored_delimiter_code)
from .utils import NotInScopeError, ascii_characters
from . import evaluator as evaler


def check_type(type_, value):
    # TODO: Make type checking more strict, and do in more places.
    if type_ in (Instructions.count.value,
                 Instructions.dimen.value,
                 Instructions.integer_parameter.value,
                 Instructions.dimen_parameter.value,
                 Instructions.special_integer.value,
                 Instructions.special_dimen.value):
        expected_type = int
    elif type_ in (Instructions.skip.value,
                   Instructions.mu_skip.value,
                   Instructions.glue_parameter.value,
                   Instructions.mu_glue_parameter.value):
        expected_type = dict
    elif type_ in (Instructions.toks.value,
                   Instructions.token_parameter.value):
        expected_type = list
    elif type_ == Instructions.set_box.value:
        expected_type = AbstractBox
    else:
        raise ValueError(f'Asked to check unknown type: {type_}')
    if not isinstance(value, expected_type):
        raise TypeError(f'Value "{value}" has wrong type: {type(value)}; '
                        f'expected {expected_type}')


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
            Instructions.set_box.value: init_register(),
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
        # TODO: Correct behaviour is more subtle than this. Getting a void box
        # should not raise an error, at least in some circumstances.
        # Do simplest implementation to get by.
        if type_ != Instructions.set_box.value and value is None:
            raise NotInScopeError(f'No value in register number {i} of type {type_}')
        return value

    def pop(self, type_, i):
        """Like `get`, but empty the register after retrieval. It's used by
        \box when retrieving boxes."""
        value = self.get(type_, i)
        self._set(type_, i, None)
        return value

    def _set(self, type_, i, value):
        register = self._check_and_get_register(type_)
        register[i] = value

    def set(self, type_, i, value):
        # Check value matches what register is meant to hold.
        check_type(type_, value)
        # Check key already exists.
        self._check_and_get_register_value(type_, i)
        self._set(type_, i, value)


# End of registers.

# Start of codes.

def get_unset_ascii_char_dict():
    return {c: None for c in ascii_characters}


class Codes:

    def __init__(self,
                 char_to_cat,
                 char_to_math_code,
                 lower_case_code, upper_case_code,
                 space_factor_code,
                 delimiter_code,
                 ):
        self.code_type_to_char_map = {
            Instructions.cat_code.value: char_to_cat,
            Instructions.math_code.value: char_to_math_code,
            Instructions.upper_case_code.value: upper_case_code,
            Instructions.lower_case_code.value: lower_case_code,
            Instructions.space_factor_code.value: space_factor_code,
            Instructions.delimiter_code.value: delimiter_code,
        }

    @staticmethod
    def default_initial_cat_codes():
        char_to_cat = get_unset_ascii_char_dict()
        char_to_cat.update({c: CatCode.other for c in ascii_characters})
        char_to_cat.update({let: CatCode.letter for let in ascii_letters})

        char_to_cat['\\'] = CatCode.escape
        char_to_cat[' '] = CatCode.space
        char_to_cat['%'] = CatCode.comment
        char_to_cat[WeirdChar.null.value] = CatCode.ignored
        # NON-STANDARD
        char_to_cat[WeirdChar.line_feed.value] = CatCode.end_of_line
        char_to_cat[WeirdChar.carriage_return.value] = CatCode.end_of_line
        char_to_cat[WeirdChar.delete.value] = CatCode.invalid
        return char_to_cat

    @staticmethod
    def default_initial_math_codes():
        char_to_math_code = get_unset_ascii_char_dict()
        for i, c in enumerate(ascii_characters):
            if c in ascii_letters:
                family = 1
            else:
                family = 0
            if c in (ascii_letters + digits):
                math_class = MathClass.variable_family
            else:
                math_class = MathClass.ordinary
            glyph_code = GlyphCode(family=family, position=i)
            char_to_math_code[i] = MathCode(math_class, glyph_code)
            # TODO: handle special active_math_code value,
            # page 155 of The TeXbook.
        return char_to_math_code

    @staticmethod
    def default_initial_case_codes():
        lower_case_code = get_unset_ascii_char_dict()
        upper_case_code = get_unset_ascii_char_dict()
        initial_vals = {c: chr(0) for c in ascii_characters}
        lower_case_code.update(initial_vals)
        upper_case_code.update(initial_vals)
        for lower, upper in zip(ascii_lowercase, ascii_uppercase):
            lower_case_code[lower] = lower
            upper_case_code[upper] = upper
            lower_case_code[upper] = lower
            upper_case_code[lower] = upper
        return lower_case_code, upper_case_code

    @staticmethod
    def default_initial_space_factor_codes():
        space_factor_code = get_unset_ascii_char_dict()
        for c in ascii_characters:
            space_factor_code[c] = 999 if c in ascii_uppercase else 1000
        return space_factor_code

    @staticmethod
    def default_initial_delimiter_codes():
        delimiter_code = get_unset_ascii_char_dict()
        delimiter_code.update({c: not_a_delimiter_code for c in ascii_characters})
        delimiter_code['.'] = ignored_delimiter_code
        return delimiter_code

    @classmethod
    def default_initial(cls):
        char_to_cat = cls.default_initial_cat_codes()
        char_to_math_code = cls.default_initial_math_codes()
        lower_case_code, upper_case_code = cls.default_initial_case_codes()
        space_factor_code = cls.default_initial_space_factor_codes()
        delimiter_code = cls.default_initial_delimiter_codes()
        return cls(char_to_cat,
                   char_to_math_code,
                   lower_case_code,
                   upper_case_code,
                   space_factor_code,
                   delimiter_code)

    @classmethod
    def default_local(cls, enclosing_scope):
        char_to_cat = get_unset_ascii_char_dict()
        char_to_math_code = get_unset_ascii_char_dict()
        lower_case_code = get_unset_ascii_char_dict()
        upper_case_code = get_unset_ascii_char_dict()
        space_factor_code = get_unset_ascii_char_dict()
        delimiter_code = get_unset_ascii_char_dict()
        return cls(char_to_cat,
                   char_to_math_code,
                   lower_case_code,
                   upper_case_code,
                   space_factor_code,
                   delimiter_code)

    def get(self, code_type, char):
        value = self._check_and_get_char_map_value(code_type, char)
        if value is None:
            raise NotInScopeError(f'No value in codes {code_type}, character {char}')
        return value

    def set(self, code_type, char, code):
        # Check key already exists.
        self._check_and_get_char_map_value(code_type, char)
        char_map = self._check_and_get_char_map(code_type)
        char_map[char] = code

    def set_by_nrs(self, code_type, char_size, code_size):
        """Convenience function to allow defining the character, and the target
        code, by integers, rather than their enum members, or whatever type a
        code's contents is."""
        char = chr(char_size)
        code = self._code_size_to_code(code_type, code_size)
        self.set(code_type, char, code)

    # Some inelegant but handy getters and setters.

    def get_cat_code(self, char):
        return self.get(Instructions.cat_code.value, char)

    def get_upper_case_code(self, char):
        return self.get(Instructions.upper_case_code.value, char)

    def get_lower_case_code(self, char):
        return self.get(Instructions.lower_case_code.value, char)

    def get_space_factor_code(self, char):
        return self.get(Instructions.space_factor_code.value, char)

    def set_cat_code(self, char, code):
        self.set(Instructions.cat_code.value, char, code)

    def set_upper_case_code(self, char, code):
        self.set(Instructions.upper_case_code.value, char, code)

    def set_lower_case_code(self, char, code):
        self.set(Instructions.lower_case_code.value, char, code)

    def set_space_factor_code(self, char, code):
        self.set(Instructions.space_factor_code.value, char, code)

    # End of inelegance.

    def _code_size_to_code(self, code_type, code_size):
        if code_type == Instructions.cat_code.value:
            return CatCode(code_size)
        elif code_type == Instructions.math_code.value:
            parts = evaler.split_hex_code(code_size,
                                          hex_length=4, inds=(1, 2))
            math_class_i, family, position = parts
            math_class = MathClass(math_class_i)
            glyph_code = GlyphCode(family, position)
            return MathCode(math_class, glyph_code)
        elif code_type in (Instructions.upper_case_code.value,
                           Instructions.lower_case_code.value):
            return chr(code_size)
        elif code_type == Instructions.space_factor_code.value:
            return code_size
        elif code_type == Instructions.delimiter_code.value:
            parts = evaler.split_hex_code(code_size,
                                          hex_length=6, inds=(1, 3, 4))
            small_family, small_position, large_family, large_position = parts
            small_glyph_code = GlyphCode(small_family, small_position)
            large_glyph_code = GlyphCode(large_family, large_position)
            return DelimiterCode(small_glyph_code, large_glyph_code)
        else:
            raise ValueError(f'Unknown code type: {code_type}')

    def _check_and_get_char_map(self, code_type):
        if code_type not in self.code_type_to_char_map:
            raise ValueError(f'No codes of type {code_type}')
        return self.code_type_to_char_map[code_type]

    def _check_and_get_char_map_value(self, code_type, char):
        char_map = self._check_and_get_char_map(code_type)
        if char not in char_map:
            raise ValueError(f'Character {char} not in codes {code_type}')
        return char_map[char]

# End of codes.

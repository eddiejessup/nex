from enum import Enum

from .codes import get_initial_codes, get_local_codes
from .registers import get_initial_registers, get_local_registers
from .tex_parameters import get_initial_parameters, get_local_parameters
from .fonts import (get_initial_font_state,
                    get_local_font_state)
from .router import get_initial_router, get_local_router


class Operation(Enum):
    advance = 1


def operate(object_operand, by_operand, operation):
    if operation == Operation.advance:
        result = object_operand + by_operand
    else:
        raise NotImplementedError
    return result


class NotInScopeError(Exception):
    pass


class ScopedAccessor:

    def __init__(self, initial_accessor, get_local_accessor_func):
        self.scopes = [initial_accessor]
        self.get_local_accessor = get_local_accessor_func

    def push_scope(self, scope):
        self.scopes.append(scope)

    def push_new_scope(self):
        scope = self.get_local_accessor(self.scope)
        self.scopes.append(scope)

    def pop_scope(self):
        self.scopes.pop()

    @property
    def scope(self):
        return self.scopes[-1]

    @property
    def global_scope(self):
        return self.scopes[0]

    def get_scopes(self, is_global):
        # Here seems the correct place to explain the behaviour of \global.
        # Maybe this quote from the TeXBook will help:
        # "In general, \global makes the immediately following definition
        # pertain to all existing groups, not just to the innermost one."
        return self.scopes if is_global else [self.scope]

    def try_scope_func_until_success(self, func_name, *args, **kwargs):
        for scope in reversed(self.scopes):
            f = getattr(scope, func_name)
            try:
                v = f(*args, **kwargs)
            except (NotInScopeError, KeyError):
                pass
            else:
                return v
        import pdb; pdb.set_trace()

    def try_scope_attr_until_success(self, attr_name):
        for scope in reversed(self.scopes):
            try:
                a = getattr(scope, attr_name)
            except (NotInScopeError, AttributeError):
                pass
            else:
                return a
        import pdb; pdb.set_trace()


class ScopedCodes(ScopedAccessor):

    @classmethod
    def from_defaults(cls):
        return cls(get_initial_codes(), get_local_codes)

    def set_code(self, is_global, code_type, char, code):
        code_type_to_func_map = {
            'CAT_CODE': 'set_cat_code',
            'MATH_CODE': 'set_math_code',
            'UPPER_CASE_CODE': 'set_upper_case_code',
            'LOWER_CASE_CODE': 'set_lower_case_code',
            'SPACE_FACTOR_CODE': 'set_space_factor_code',
            'DELIMITER_CODE': 'set_delimiter_code',
        }
        func_name = code_type_to_func_map[code_type]
        for scope in self.get_scopes(is_global):
            set_func = getattr(scope, func_name)
            set_func(char, code)

    def get_cat_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_cat_code', *args, **kwargs)

    def get_math_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_math_code', *args, **kwargs)

    def get_lower_case_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_lower_case_code', *args, **kwargs)

    def get_upper_case_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_upper_case_code', *args, **kwargs)

    def get_space_factor_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_space_factor_code', *args, **kwargs)

    def get_delimiter_code(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_delimiter_code', *args, **kwargs)


class ScopedRegisters(ScopedAccessor):

    @classmethod
    def from_defaults(cls):
        return cls(get_initial_registers(), get_local_registers)

    def get_register_value(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_register_value', *args, **kwargs)

    def set_register_value(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.set_register_value(*args, **kwargs)

    def modify_register_value(self, is_global, type_, i, by_operand,
                              operation):
        # The in-place arithmetic is a bit strange.
        # The register operand is defined as normal: the most-locally defined
        # register.
        # But the result should create/update the register in the strictly
        # local scope.
        # If the operation is \global, the operation is done as above,
        # on the most-local register value; then the strictly-local register
        # value becomes the value for all scopes.
        # That is to say, the \global bit is acted on last.
        object_operand = self.get_register_value(type_, i)
        result = operate(object_operand, by_operand, operation)
        self.set_register_value(is_global, type_, i, result)


class ScopedFontState(ScopedAccessor):

    @classmethod
    def from_defaults(cls):
        return cls(get_initial_font_state(), get_local_font_state)

    @property
    def current_font_id(self, *args, **kwargs):
        return self.try_scope_attr_until_success('current_font_id')

    def set_current_font(self, is_global, *args, **kwargs):
        scopes = self.get_scopes(is_global)
        for scope in scopes:
            scope.set_current_font(*args, **kwargs)

    def set_font_family(self, is_global, *args, **kwargs):
        scopes = self.get_scopes(is_global)
        for scope in scopes:
            scope.set_font_family(*args, **kwargs)


class ScopedRouter(ScopedAccessor):

    @classmethod
    def from_defaults(cls):
        return cls(get_initial_router(), get_local_router)

    def lookup_control_sequence(self, *args, **kwargs):
        return self.try_scope_func_until_success('lookup_control_sequence',
                                                 *args, **kwargs)

    def set_macro(self, name, replacement_text, parameter_text, def_type, prefixes):
        # TODO: Consider \globaldefs integer parameter.
        # TODO: do something about \outer. Although it seems a bit fussy...
        # TODO: do something about \long. Although the above also applies...
        is_global = def_type.type in ('G_DEF', 'X_DEF') or 'GLOBAL' in prefixes
        # Need to set for all outer scopes, in case we have already defined
        # the macro in a non-global scope.
        for scope in self.get_scopes(is_global):
            macro_token = scope.set_macro(name,
                                          replacement_text=replacement_text,
                                          parameter_text=parameter_text,
                                          def_type=def_type,
                                          prefixes=prefixes)
        return macro_token

    def do_short_hand_definition(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            macro_token = scope.do_short_hand_definition(*args, **kwargs)
        return macro_token

    def define_new_font_control_sequence(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            macro_token = scope.define_new_font_control_sequence(*args, **kwargs)
        return macro_token

    def do_let_assignment(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.do_let_assignment(*args, **kwargs)


class ScopedParameters(ScopedAccessor):

    @classmethod
    def from_defaults(cls):
        return cls(get_initial_parameters(), get_local_parameters)

    def get_parameter_value(self, *args, **kwargs):
        return self.try_scope_func_until_success('get_parameter_value', *args, **kwargs)

    def set_parameter(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.set_parameter_value(*args, **kwargs)

    def modify_parameter_value(self, is_global, parameter, by_operand,
                               operation):
        # We assume the same applies for parameters as for registers in
        # `modify_register_value`.
        object_operand = self.get_parameter_value(parameter)
        result = operate(object_operand, by_operand, operation)
        self.set_parameter(is_global, parameter, result)

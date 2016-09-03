from codes import get_initial_codes, get_local_codes
from registers import get_initial_registers, get_local_registers
from fonts import GlobalFontState, get_initial_font_state, get_local_font_state


class NotInScopeError(Exception):
    pass


class Scope(object):

    def __init__(self, codes, registers, font_state):
        self.codes = codes
        self.registers = registers
        self.font_state = font_state

    # Codes interface.

    def defer_to_codes(self, func_name, *args, **kwargs):
        f = getattr(self.codes, func_name)
        return f(*args, **kwargs)

    def set_cat_code(self, *args, **kwargs):
        self.defer_to_codes('set_cat_code', *args, **kwargs)

    def set_math_code(self, *args, **kwargs):
        self.defer_to_codes('set_math_code', *args, **kwargs)

    def set_upper_case_code(self, *args, **kwargs):
        self.defer_to_codes('set_upper_case_code', *args, **kwargs)

    def set_lower_case_code(self, *args, **kwargs):
        self.defer_to_codes('set_lower_case_code', *args, **kwargs)

    def set_space_factor_code(self, *args, **kwargs):
        self.defer_to_codes('set_space_factor_code', *args, **kwargs)

    def set_delimiter_code(self, *args, **kwargs):
        self.defer_to_codes('set_delimiter_code', *args, **kwargs)

    def get_cat_code(self, *args, **kwargs):
        return self.defer_to_codes('get_cat_code', *args, **kwargs)

    def get_math_code(self, *args, **kwargs):
        return self.defer_to_codes('get_math_code', *args, **kwargs)

    def get_upper_case_code(self, *args, **kwargs):
        return self.defer_to_codes('get_upper_case_code', *args, **kwargs)

    def get_lower_case_code(self, *args, **kwargs):
        return self.defer_to_codes('get_lower_case_code', *args, **kwargs)

    def get_space_factor_code(self, *args, **kwargs):
        return self.defer_to_codes('get_space_factor_code', *args, **kwargs)

    def get_delimiter_code(self, *args, **kwargs):
        return self.defer_to_codes('get_delimiter_code', *args, **kwargs)

    # Register interface.

    # TODO: maybe just have outside things address .registers directly.
    def defer_to_registers(self, func_name, *args, **kwargs):
        f = getattr(self.registers, func_name)
        return f(*args, **kwargs)

    def get_register_value(self, *args, **kwargs):
        return self.defer_to_registers('get_register_value', *args, **kwargs)

    def set_register_value(self, *args, **kwargs):
        return self.defer_to_registers('set_register_value', *args, **kwargs)

    def advance_register_value(self, *args, **kwargs):
        return self.defer_to_registers('advance_register_value', *args, **kwargs)


def get_initial_scope():
    codes = get_initial_codes()
    registers = get_initial_registers()
    font_state = get_initial_font_state()
    initial_scope = Scope(codes, registers, font_state)
    return initial_scope


def get_local_scope():
    codes = get_local_codes()
    registers = get_local_registers()
    font_state = get_local_font_state()
    local_scope = Scope(codes, registers, font_state)
    return local_scope


class GlobalState(object):

    def __init__(self):
        self.global_font_state = GlobalFontState()
        self.scopes = []
        initial_scope = get_initial_scope()
        self.push_scope(initial_scope)

    def push_scope(self, scope):
        self.scopes.append(scope)

    def push_new_scope(self):
        scope = get_local_scope()
        self.scopes.append(scope)

    def pop_scope(self):
        self.scopes.pop()

    @property
    def scope(self):
        return self.scopes[-1]

    def set_cat_code(self, *args, **kwargs):
        self.scope.set_cat_code(*args, **kwargs)

    def set_math_code(self, *args, **kwargs):
        self.scope.set_math_code(*args, **kwargs)

    def set_upper_case_code(self, *args, **kwargs):
        self.scope.set_upper_case_code(*args, **kwargs)

    def set_lower_case_code(self, *args, **kwargs):
        self.scope.set_lower_case_code(*args, **kwargs)

    def set_space_factor_code(self, *args, **kwargs):
        self.scope.set_space_factor_code(*args, **kwargs)

    def set_delimiter_code(self, *args, **kwargs):
        self.scope.set_delimiter_code(*args, **kwargs)

    def try_scope_until_success(self, func_name, *args, **kwargs):
        for scope in reversed(self.scopes):
            f = getattr(scope, func_name)
            try:
                v = f(*args, **kwargs)
            except (NotInScopeError, KeyError):
                pass
            else:
                return v
        import pdb; pdb.set_trace()

    # Codes.

    def get_cat_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_cat_code', *args, **kwargs)

    def get_math_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_math_code', *args, **kwargs)

    def get_lower_case_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_lower_case_code', *args, **kwargs)

    def get_upper_case_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_upper_case_code', *args, **kwargs)

    def get_space_factor_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_space_factor_code', *args, **kwargs)

    def get_delimiter_code(self, *args, **kwargs):
        return self.try_scope_until_success('get_delimiter_code', *args, **kwargs)

    # Registers.

    def get_register_value(self, *args, **kwargs):
        return self.try_scope_until_success('get_register_value', *args, **kwargs)

    def set_register_value(self, *args, **kwargs):
        self.scope.set_register_value(*args, **kwargs)

    def advance_register_value(self, *args, **kwargs):
        self.try_scope_until_success('advance_register_value', *args, **kwargs)

    # Fonts.

    def set_current_font(self, *args, **kwargs):
        self.scope.font_state.set_current_font(*args, **kwargs)

    def set_font_family(self, *args, **kwargs):
        self.scope.font_state.set_font_family(*args, **kwargs)

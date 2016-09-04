from codes import get_initial_codes, get_local_codes
from registers import get_initial_registers, get_local_registers
from fonts import GlobalFontState, get_initial_font_state, get_local_font_state
from expander import get_initial_expander, get_local_expander


class NotInScopeError(Exception):
    pass


class Scope(object):

    def __init__(self, codes, registers, font_state, expander):
        self.codes = codes
        self.registers = registers
        self.font_state = font_state
        self.expander = expander

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

    # Expander interface.

    # TODO: maybe just have outside things address .expander directly.
    def defer_to_expander(self, func_name, *args, **kwargs):
        f = getattr(self.expander, func_name)
        return f(*args, **kwargs)

    def expand_macro_to_token_list(self, *args, **kwargs):
        return self.defer_to_expander('expand_macro_to_token_list', *args, **kwargs)

    def resolve_control_sequence_to_token(self, *args, **kwargs):
        return self.defer_to_expander('resolve_control_sequence_to_token', *args, **kwargs)

    def set_macro(self, *args, **kwargs):
        return self.defer_to_expander('set_macro', *args, **kwargs)

    def do_short_hand_definition(self, *args, **kwargs):
        return self.defer_to_expander('do_short_hand_definition', *args, **kwargs)

    def do_let_assignment(self, *args, **kwargs):
        return self.defer_to_expander('do_let_assignment', *args, **kwargs)

    def define_new_font_control_sequence(self, *args, **kwargs):
        return self.defer_to_expander('define_new_font_control_sequence', *args, **kwargs)

    def get_parameter_value(self, *args, **kwargs):
        return self.defer_to_expander('get_parameter_value', *args, **kwargs)

    def set_parameter(self, *args, **kwargs):
        return self.defer_to_expander('set_parameter', *args, **kwargs)


def get_initial_scope():
    codes = get_initial_codes()
    registers = get_initial_registers()
    font_state = get_initial_font_state()
    expander = get_initial_expander()
    initial_scope = Scope(codes, registers, font_state, expander)
    return initial_scope


def get_local_scope(enclosing_scope):
    codes = get_local_codes()
    registers = get_local_registers()
    font_state = get_local_font_state()
    expander = get_local_expander(enclosing_scope)
    local_scope = Scope(codes, registers, font_state, expander)
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
        scope = get_local_scope(self.scope)
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
        return self.scopes if is_global else [self.scope]

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

    def get_advanced_register_value(self, *args, **kwargs):
        return self.try_scope_until_success('get_advanced_register_value', *args, **kwargs)

    def set_register_value(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.set_register_value(*args, **kwargs)

    def advance_register_value(self, is_global, type_, i, value):
        # The in-place arithmetic is a bit strange.
        # The operand is defined as normal: the most-locally defined register.
        # But the result should create/update the register in
        # the strictly local scope.
        # If the operation is \global, the operation is done as above,
        # on the most-local register value; then the strictly-local register
        # value becomes the value for all scopes.
        # That is to say, the \global bit is acted on last.
        result = self.get_advanced_register_value(type_, i, value)
        self.set_register_value(is_global, type_, i, result)

    # Fonts.

    def set_current_font(self, *args, **kwargs):
        self.scope.font_state.set_current_font(*args, **kwargs)

    def set_font_family(self, *args, **kwargs):
        self.scope.font_state.set_font_family(*args, **kwargs)

    # Expander.

    def expand_macro_to_token_list(self, *args, **kwargs):
        return self.try_scope_until_success('expand_macro_to_token_list', *args, **kwargs)

    def resolve_control_sequence_to_token(self, *args, **kwargs):
        return self.try_scope_until_success('resolve_control_sequence_to_token', *args, **kwargs)

    def set_macro(self, name, definition_token, prefixes):
        # TODO: Consider of \globaldefs integer parameter.
        # TODO: do something about \outer. Although it seems a bit fussy...
        # TODO: do something about \long. Although the above also applies...
        def_type = definition_token.value['def_type']
        is_global = def_type in ('G_DEF', 'X_DEF') or 'GLOBAL' in prefixes
        # TODO: do something about this.
        is_expanded = def_type in ('E_DEF', 'X_DEF')
        # Need to set for all outer scopes, in case we have already defined
        # the macro in a non-global scope.
        for scope in self.get_scopes(is_global):
            macro_token = scope.set_macro(name, definition_token, prefixes)
        return macro_token

    def do_short_hand_definition(self, is_global, *args, **kwargs):
        scopes = self.get_scopes(is_global)
        for scope in scopes:
            macro_token = self.scope.do_short_hand_definition(*args, **kwargs)
        return macro_token

    def do_let_assignment(self, *args, **kwargs):
        self.scope.do_let_assignment(*args, **kwargs)

    def get_parameter_value(self, *args, **kwargs):
        return self.try_scope_until_success('get_parameter_value', *args, **kwargs)

    def set_parameter(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.set_parameter(*args, **kwargs)

    # Hybrid, expander and global fonts.

    def define_new_font(self, name, file_name, at_clause):
        new_font_id = self.global_font_state.define_new_font(file_name,
                                                             at_clause)
        definition_token = self.scope.expander.define_new_font_control_sequence(name,
                                                                                new_font_id)
        return definition_token

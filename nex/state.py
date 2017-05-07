from enum import Enum

from .codes import get_initial_codes, get_local_codes
from .registers import get_initial_registers, get_local_registers
from .tex_parameters import get_initial_parameters, get_local_parameters
from .fonts import (GlobalFontState, get_initial_font_state,
                    get_local_font_state)
from .router import get_initial_router, get_local_router


class Mode(Enum):
    # Building the main vertical list.
    vertical = 'V'
    # Building a vertical list for a vbox.
    internal_vertical = 'IV'
    # Building a horizontal list for a paragraph.
    horizontal = 'H'
    # Building a horizontal list for an hbox.
    restricted_horizontal = 'RH'
    # Building a formula to be placed in a horizontal list.
    math = 'M'
    # Building a formula to be placed on a line by itself,
    # interrupting the current paragraph.
    display_math = 'DM'


vertical_modes = (Mode.vertical, Mode.internal_vertical)
horizontal_modes = (Mode.horizontal, Mode.restricted_horizontal)


class Group(Enum):

    # Note, this is *not* the same as 'global scope'. We could enter
    # sub-groups that do not start a new scope, such as a math group.
    outside = 0
    # For 'local structure'.
    local = 1
    # \hbox{...}.
    h_box = 2
    # \hbox{...} in vertical mode.
    adjusted_h_box = 3
    # \vbox{...}.
    v_box = 4
    # \vtop{...}.
    v_top = 5
    # \halign{...} and \valign{...}.
    align = 6
    # \noalign{...}.
    no_align = 7
    # Output routine.
    output = 8
    # For things such as '^{...}'
    math = 9
    # \discretionary{...}{...}{...}.
    discretionary = 10
    # \insert{...} and \vadjust{...}
    insert = 11
    # \vcenter{...}
    v_center = 12
    # \mathchoice{...}{...}{...}{...}
    math_choice = 13
    # \begingroup...\endgroup
    local_verbose = 14
    # $...$
    math_shift = 15
    # \left...\right
    math_left_right = 16


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


class Scope(object):

    def __init__(self, codes, registers, parameters, font_state, cs_router):
        self.codes = codes
        self.registers = registers
        self.parameters = parameters
        self.font_state = font_state
        self.cs_router = cs_router

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

    # Parameter interface.

    # TODO: maybe just have outside things address .parameters directly.
    def defer_to_parameters(self, func_name, *args, **kwargs):
        f = getattr(self.parameters, func_name)
        return f(*args, **kwargs)

    def get_parameter_value(self, *args, **kwargs):
        return self.defer_to_parameters('get_parameter_value', *args, **kwargs)

    def set_parameter_value(self, *args, **kwargs):
        return self.defer_to_parameters('set_parameter_value', *args, **kwargs)

    # Font interface.

    def defer_to_font_state(self, func_name, *args, **kwargs):
        f = getattr(self.font_state, func_name)
        return f(*args, **kwargs)

    @property
    def current_font_id(self):
        return self.font_state.current_font_id

    # TODO: maybe just have outside things address .router directly.
    def defer_to_router(self, func_name, *args, **kwargs):
        f = getattr(self.cs_router, func_name)
        return f(*args, **kwargs)

    def resolve_control_sequence_to_token(self, *args, **kwargs):
        return self.defer_to_router('resolve_control_sequence_to_token',
                                    *args, **kwargs)

    def set_macro(self, *args, **kwargs):
        self.defer_to_router('set_macro', *args, **kwargs)

    def do_short_hand_definition(self, *args, **kwargs):
        self.defer_to_router('do_short_hand_definition', *args, **kwargs)

    def do_let_assignment(self, *args, **kwargs):
        self.defer_to_router('do_let_assignment', *args, **kwargs)

    def define_new_font_control_sequence(self, *args, **kwargs):
        self.defer_to_router('define_new_font_control_sequence', *args, **kwargs)


def get_initial_scope(global_font_state):
    codes = get_initial_codes()
    parameters = get_initial_parameters()
    registers = get_initial_registers()
    font_state = get_initial_font_state(global_font_state)
    router = get_initial_router()
    initial_scope = Scope(codes, registers, parameters, font_state, router)
    return initial_scope


def get_local_scope(enclosing_scope):
    codes = get_local_codes()
    registers = get_local_registers()
    parameters = get_local_parameters()
    font_state = get_local_font_state()
    router = get_local_router(enclosing_scope)
    local_scope = Scope(codes, registers, parameters, font_state, router)
    return local_scope


class GlobalState(object):

    def __init__(self, font_search_paths):
        self.global_font_state = GlobalFontState(font_search_paths)
        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.modes = [(Mode.vertical, [])]
        self.groups = [Group.outside]
        self.scopes = []
        initial_scope = get_initial_scope(self.global_font_state)
        self.push_scope(initial_scope)

    # Mode.

    @property
    def mode(self):
        return self.modes[-1][0]

    @property
    def _layout_list(self):
        return self.modes[-1][1]

    def push_mode(self, mode):
        self.modes.append((mode, []))

    def pop_mode(self):
        mode, layout_list = self.modes.pop()
        return layout_list

    def append_to_list(self, item):
        self._layout_list.append(item)

    # Group.

    @property
    def group(self):
        return self.groups[-1]

    def push_group(self, group):
        self.groups.append(group)

    def pop_group(self):
        return self.groups.pop()

    # Scope.

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

    # Codes.

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

    # Registers.

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

    # Parameters.

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

    # Fonts.

    @property
    def current_font(self, *args, **kwargs):
        current_font_id = self.try_scope_attr_until_success('current_font_id')
        current_font = self.global_font_state.fonts[current_font_id]
        return current_font

    def set_current_font(self, is_global, *args, **kwargs):
        scopes = self.get_scopes(is_global)
        for scope in scopes:
            scope.font_state.set_current_font(*args, **kwargs)

    def set_font_family(self, is_global, *args, **kwargs):
        scopes = self.get_scopes(is_global)
        for scope in scopes:
            scope.font_state.set_font_family(*args, **kwargs)

    # Router.

    def expand_macro_to_token_list(self, *args, **kwargs):
        return self.try_scope_func_until_success('expand_macro_to_token_list', *args, **kwargs)

    def resolve_control_sequence_to_token(self, *args, **kwargs):
        return self.try_scope_func_until_success('resolve_control_sequence_to_token', *args, **kwargs)

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

    def do_let_assignment(self, is_global, *args, **kwargs):
        for scope in self.get_scopes(is_global):
            scope.do_let_assignment(*args, **kwargs)

    # Hybrid, router and global fonts.

    def define_new_font(self, is_global, name, file_name, at_clause):
        new_font_id = self.global_font_state.define_new_font(file_name,
                                                             at_clause)
        for scope in self.get_scopes(is_global):
            scope.cs_router.define_new_font_control_sequence(name, new_font_id)
        return new_font_id

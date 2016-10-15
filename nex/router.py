from .common import BuiltToken, TerminalToken, NonTerminalToken, InternalToken
from .utils import get_unique_id, NoSuchControlSequence
from .tex_parameters import parameter_type_to_names
from .typer import (control_sequence_lex_type, char_cat_lex_type,
                    short_hand_def_to_token_map, font_def_token_type,
                    primitive_control_sequences_map,
                    terminal_primitive_control_sequences_map,
                    )


def make_simple_definition_token(name, tokens):
    def_text_token = BuiltToken(type_='definition_text',
                                value={'parameter_text': [],
                                       'replacement_text': tokens})
    def_token = BuiltToken(type_='definition',
                           value={'name': name,
                                  'text': def_text_token})
    return def_token


def make_control_sequence_call_token(Cls, type_, name):
    return Cls(type_=type_, value={'name': name,
                                   'lex_type': control_sequence_lex_type})


primitive_canon_tokens = {}
for prim_canon_name, prim_type in primitive_control_sequences_map.items():
    # Terminals are tokens that may be passed to the parser. Non-terminals
    # are tokens that will be consumed by the banisher before the parser
    # sees them.
    is_terminal = prim_canon_name in terminal_primitive_control_sequences_map
    TokenCls = TerminalToken if is_terminal else NonTerminalToken
    primitive_canon_token = make_control_sequence_call_token(
        TokenCls, prim_type, prim_canon_name)
    primitive_canon_tokens[prim_canon_name] = primitive_canon_token


def make_route_token(type_, route_id):
    return InternalToken(type_=type_, value=route_id)


def get_initial_router():
    control_sequences = {}

    macros = {}
    let_chars = {}

    parameters = {}
    for param_type, param_canonical_names in parameter_type_to_names.items():
        for param_canonical_name in param_canonical_names:
            # Add a router for the canonical name to the primitive.
            route_id = param_canonical_name
            route_token = make_route_token('parameter', route_id)
            control_sequences[param_canonical_name] = route_token

            param_canon_token = TerminalToken(
                type_=param_type,
                value={'canonical_name': param_canonical_name,
                       'name': param_canonical_name}
            )
            parameters[route_id] = param_canon_token

    primitives = {}
    for prim_canon_name, prim_canon_token in primitive_canon_tokens.items():
        # Add a router for the canonical name to the primitive.
        route_id = prim_canon_name
        route_token = make_route_token('primitive', route_id)
        control_sequences[prim_canon_name] = route_token

        # Make that route resolve to the primitive canonical token.
        primitives[route_id] = prim_canon_token

    router = CSRouter(control_sequences,
                      macros, let_chars, parameters, primitives,
                      enclosing_scope=None)
    return router


def get_local_router(enclosing_scope):
    control_sequences = {}

    macros = {}
    let_chars = {}
    parameters = {}
    primitives = {}

    router = CSRouter(control_sequences,
                      macros, let_chars, parameters, primitives,
                      enclosing_scope)
    return router


class CSRouter(object):

    def __init__(self, control_sequences,
                 macros, let_chars, parameters, primitives,
                 enclosing_scope=None):
        self.control_sequences = control_sequences

        self.macros = macros
        self.let_chars = let_chars
        self.parameters = parameters
        self.primitives = primitives

        self.enclosing_scope = enclosing_scope

    def _set_route_token(self, name, route_token):
        self.control_sequences[name] = route_token

    def _resolve_control_sequence_to_route_token(self, name):
        # If the route token exists in this scope, return it.
        if name in self.control_sequences:
            route_token = self.control_sequences[name]
        # Otherwise, if there's an enclosing scope, ask it for it.
        elif self.enclosing_scope is not None:
            route_token = self.enclosing_scope.cs_router._resolve_control_sequence_to_route_token(name)
        # If we are the outermost scope, the control sequence is unknown.
        else:
            raise NoSuchControlSequence(name)
        return route_token

    def _resolve_route_token_to_raw_value(self, r):
        type_ = r.type
        route_id = r.value
        value_maps_map = {
            'parameter': self.parameters,
            'primitive': self.primitives,
            'macro': self.macros,
            'let_character': self.let_chars,
        }
        value_map = value_maps_map[type_]
        try:
            v = value_map[route_id]
        except:
            v = self.enclosing_scope.cs_router._resolve_route_token_to_raw_value(r)
        return v

    def resolve_control_sequence_to_token(self, name):
        route_token = self._resolve_control_sequence_to_route_token(name)
        token = self._resolve_route_token_to_raw_value(route_token)
        # Amend canonical tokens to give them the proper control sequence
        # 'name'.
        if 'name' in token.value:
            TokenCls = token.__class__
            token = TokenCls(type_=token.type, value=token.value.copy())
            token.value['name'] = name
        return token

    def _copy_control_sequence(self, target_name, new_name):
        # Make a new control sequence that is routed to the same spot as the
        # current one.
        target_route_token = self._resolve_control_sequence_to_route_token(target_name)
        self._set_route_token(new_name, target_route_token)

    def do_let_assignment(self, new_name, target_token):
        if target_token.value['lex_type'] == control_sequence_lex_type:
            target_name = target_token.value['name']
            self._copy_control_sequence(target_name, new_name)
        elif target_token.value['lex_type'] == char_cat_lex_type:
            self._set_let_character(new_name, target_token)
        else:
            import pdb; pdb.set_trace()

    def set_macro(self, name, definition_token, prefixes=None):
        route_id = get_unique_id()
        route_token = make_route_token('macro', route_id)
        self._set_route_token(name, route_token)

        if prefixes is None:
            prefixes = set()
        macro_token = NonTerminalToken(type_='MACRO',
                                       value={'prefixes': prefixes,
                                              'definition': definition_token})
        self.macros[route_id] = macro_token
        return macro_token

    def do_short_hand_definition(self, name, def_type, code):
        def_token_type = short_hand_def_to_token_map[def_type]
        primitive_token = TerminalToken(type_=def_token_type, value=code)
        definition_token = make_simple_definition_token(name,
                                                        [primitive_token])
        macro_token = self.set_macro(name, definition_token, prefixes=None)
        return macro_token

    def _set_let_character(self, name, char_cat_token):
        route_id = get_unique_id()
        route_token = make_route_token('let_character', route_id)
        self._set_route_token(name, route_token)
        self.let_chars[route_id] = char_cat_token

    def define_new_font_control_sequence(self, name, font_id):
        # Note, this token just records the font id; the information
        # is stored in the global font state, because it has internal
        # state that might be modified later; we need to know where to get
        # at it.
        primitive_token = TerminalToken(type_=font_def_token_type,
                                        value=font_id)
        definition_token = make_simple_definition_token(name,
                                                        [primitive_token])
        # TODO: Set directly as font token, not as a macro.
        self.set_macro(name, definition_token, prefixes=None)

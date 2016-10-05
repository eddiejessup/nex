from common import Token, TerminalToken, InternalToken
from utils import get_unique_id, NoSuchControlSequence
from tex_parameters import default_parameters
from typer import (control_sequence_lex_type, char_cat_lex_type,
                       short_hand_def_to_token_map, font_def_token_type,
                       unexpanded_cs_types,
                       primitive_control_sequences_map, terminal_primitive_control_sequences_map,
                       )

undelim_macro_param_type = 'UNDELIMITED_PARAM'
delim_macro_param_type = 'DELIMITED_PARAM'
macro_param_types = (undelim_macro_param_type, delim_macro_param_type)

parameter_types = default_parameters.keys()


def is_parameter_type(type_):
    return type_ in parameter_types


def parse_parameter_text(tokens):
    p_nr = 1
    i = 0
    parameters = []
    while i < len(tokens):
        t = tokens[i]

        # The only time we should see a non-parameter, is if there is text
        # preceding the parameters proper. Anything else should be
        # gobbled down below. Ooh-err.
        # "
        # Tokens that precede the first parameter token in the parameter
        # text of a definition are required to follow the control sequence; in
        # effect, they become part of the control sequence name.
        # "
        if t.type != 'PARAMETER':
            assert p_nr == 1
            parameters.append(t)
            i += 1
            continue

        # Go forward to get the parameter number,
        # and check it is numbered correctly.
        i += 1
        t_next = tokens[i]
        if int(t_next.value['char']) != p_nr:
            raise ValueError

        # "
        # How does TeX determine where an argument stops, you ask. Answer:
        # There are two cases.
        # An undelimited parameter is followed immediately in the parameter
        # text by a parameter token, or it occurs at the very end of the
        # parameter text; [...]
        # A delimited parameter is followed in the parameter text by
        # one or more non-parameter tokens [...]
        # "
        delim_tokens = []
        i += 1
        if i < len(tokens):
            # If there are more tokens, go forward in the token list collecting
            # delimiter tokens.
            while i < len(tokens):
                d_t = tokens[i]
                if d_t.type == 'PARAMETER':
                    break
                else:
                    delim_tokens.append(d_t)
                i += 1
        type_ = (delim_macro_param_type if delim_tokens
                 else undelim_macro_param_type)
        param = InternalToken(type_=type_, value={'param_nr': p_nr,
                                                  'delim_tokens': delim_tokens})
        p_nr += 1
        parameters.append(param)
    return parameters


def parse_replacement_text(tokens):
    i = 0
    tokens_processed = []
    while i < len(tokens):
        t = tokens[i]
        if t.type == 'PARAMETER':
            i += 1
            t_next = tokens[i]
            # [...] each # must be followed by a digit that appeared after # in
            # the parameter text, or else the # should be followed by another
            # #.
            if t_next.type == 'PARAMETER':
                # TODO: I don't know if the cat-code of this should be changed.
                # Look in TeX: The Program to see what it does.
                tokens_processed.append(t_next)
            else:
                p_nr = int(t_next.value['char'])
                t = InternalToken(type_='PARAM_NUMBER', value=p_nr)
        tokens_processed.append(t)
        i += 1
    return tokens_processed


def substitute_params_with_args(replace_text, arguments):
    finished_text = []
    for i, t in enumerate(replace_text):
        if t.type == 'PARAM_NUMBER':
            param_nr = t.value
            argument_i = param_nr - 1
            argument_tokens = arguments[argument_i]
            finished_text.extend(argument_tokens)
        else:
            finished_text.append(t)
    return finished_text


def make_simple_definition_token(name, tokens):
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': [],
                                  'replacement_text': tokens})
    def_token = Token(type_='definition',
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
    TokenCls = TerminalToken if is_terminal else InternalToken
    primitive_canon_token = make_control_sequence_call_token(
        TokenCls, prim_type, prim_canon_name)
    primitive_canon_tokens[prim_canon_name] = primitive_canon_token


def get_initial_expander():
    control_sequences = {}

    macros = {}
    let_chars = {}

    parameters = {}
    for param_type, param_map in default_parameters.items():
        for param_canon_name, param_value in param_map.items():
            # Add a router for the canonical name to the primitive.
            route_id = param_canon_name
            route_token = InternalToken(type_='parameter',
                                        value=route_id)
            control_sequences[param_canon_name] = route_token

            param_canon_token = TerminalToken(
                type_=param_type,
                value={'canonical_name': param_canon_name,
                       'name': param_canon_name,
                       'value': param_value}
            )
            parameters[route_id] = param_canon_token

    primitives = {}
    for prim_canon_name, prim_canon_token in primitive_canon_tokens.items():
        # Add a router for the canonical name to the primitive.
        route_id = prim_canon_name
        route_token = InternalToken(type_='primitive', value=route_id)
        control_sequences[prim_canon_name] = route_token

        # Make that route resolve to the primitive canonical token.
        primitives[route_id] = prim_canon_token

    expander = Expander(control_sequences,
                        macros, let_chars, parameters, primitives,
                        enclosing_scope=None)
    return expander


def get_local_expander(enclosing_scope):
    control_sequences = {}

    macros = {}
    let_chars = {}
    parameters = {}
    primitives = {}

    expander = Expander(control_sequences,
                        macros, let_chars, parameters, primitives,
                        enclosing_scope)
    return expander


class Expander(object):

    def __init__(self, control_sequences,
                 macros, let_chars, parameters, primitives,
                 enclosing_scope=None):
        self.control_sequences = control_sequences

        self.macros = macros
        self.let_chars = let_chars
        self.parameters = parameters
        self.primitives = primitives

        self.enclosing_scope = enclosing_scope

    def expand_macro_to_token_list(self, name, arguments):
        token = self.resolve_control_sequence_to_token(name)
        def_token = token.value['definition']
        def_text_token = def_token.value['text']
        replace_text = def_text_token.value['replacement_text']
        finished_text = substitute_params_with_args(replace_text, arguments)
        return finished_text

    def _set_route_token(self, name, route_token):
        self.control_sequences[name] = route_token

    def _resolve_control_sequence_to_route_token(self, name):
        # If the route token exists in this scope, return it.
        if name in self.control_sequences:
            route_token = self.control_sequences[name]
        # Otherwise, if there's an enclosing scope, ask it for it.
        elif self.enclosing_scope is not None:
            route_token = self.enclosing_scope.expander._resolve_control_sequence_to_route_token(name)
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
            v = self.enclosing_scope.expander._resolve_route_token_to_raw_value(r)
        return v

    def resolve_control_sequence_to_token(self, name):
        route_token = self._resolve_control_sequence_to_route_token(name)
        type_ = route_token.type
        token = self._resolve_route_token_to_raw_value(route_token)
        # Amend canonical tokens to give them the proper control sequence
        # 'name'.
        if type_ in ('primitive',) + tuple(parameter_types):
            TokenCls = token.__class__
            token = TokenCls(type_=token.type, value=token.value.copy())
            token.value['name'] = name
        # TODO: check what happens if we \let something to a macro,
        # then call \csname on it. Do we get the original macro name?
        # Maybe need to do something like for canonical tokens above.
        return token

    def get_parameter_value(self, name):
        parameter_token = self.resolve_control_sequence_to_token(name)
        parameter_value = parameter_token.value['value']
        return parameter_value

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
            self.set_let_character(new_name, target_token)
        else:
            import pdb; pdb.set_trace()

    def set_macro(self, name, definition_token, prefixes=None):
        route_id = get_unique_id()
        route_token = InternalToken(type_='macro', value=route_id)
        self._set_route_token(name, route_token)

        if prefixes is None:
            prefixes = set()
        macro_token = InternalToken(type_='MACRO',
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

    def set_let_character(self, name, char_cat_token):
        route_id = get_unique_id()
        route_token = InternalToken(type_='let_character',
                                    value=route_id)
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

    def set_parameter(self, name, value):
        parameter_token = self.resolve_control_sequence_to_token(name)
        parameter_token.value['value'] = value

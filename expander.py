from common import Token, TerminalToken, InternalToken
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


def parse_parameter_text(tokens):
    p_nr = 1
    i = 0
    tokens_processed = []
    while i < len(tokens):
        t = tokens[i]
        if t.type == 'PARAMETER':
            i += 1
            t_next = tokens[i]
            if int(t_next.value['char']) != p_nr:
                raise ValueError
            # How does TeX determine where an argument stops, you ask. Answer:
            # There are two cases.
            # An undelimited parameter is followed immediately in the parameter
            # text by a parameter token, or it occurs at the very end of the
            # parameter text; [...]
            if i == len(tokens) - 1:
                type_ = undelim_macro_param_type
            else:
                t_after = tokens[i + 1]
                if t_after.type == 'PARAMETER':
                    type_ = undelim_macro_param_type
                # A delimited parameter is followed in the parameter text by
                # one or more non-parameter tokens [...]
                else:
                    type_ = delim_macro_param_type
            t = InternalToken(type_=type_, value=p_nr)
            p_nr += 1
        tokens_processed.append(t)
        i += 1
    return tokens_processed


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
                raise NotImplementedError
            else:
                p_nr = int(t_next.value['char'])
                t = InternalToken(type_='PARAM_NUMBER', value=p_nr)
        tokens_processed.append(t)
        i += 1
    return tokens_processed


def get_nr_params(param_text):
    return sum(t.type in macro_param_types for t in param_text)


def parse_argument_text(argument_text, parameter_text):
    # Just assume all undelimited arguments
    return argument_text


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
    return Cls(type_=type_, value={'name': name})


def get_initial_expander():
    control_sequences = {}

    macros = {}
    let_chars = {}

    parameter_maps = default_parameters.copy()
    for param_type, param_map in parameter_maps.items():
        for param_canon_name in param_map:
            route_token = InternalToken(type_='parameter',
                                        value={'parameter_type': param_type,
                                               'parameter_canonical_name': param_canon_name})
            control_sequences[param_canon_name] = route_token

    primitives = {}
    for prim_canon_name, prim_type in primitive_control_sequences_map.items():
        # Add a router for the canonical name to the primitive.
        route_token = InternalToken(type_='primitive', value=prim_canon_name)
        control_sequences[prim_canon_name] = route_token

        # Terminals are tokens that may be passed to the parser. Non-terminals
        # are tokens that will be consumed by the banisher before the parser
        # sees them.
        is_terminal = prim_canon_name in terminal_primitive_control_sequences_map
        TokenCls = TerminalToken if is_terminal else InternalToken
        primitive_canon_token = make_control_sequence_call_token(
            TokenCls, prim_type, prim_canon_name)
        primitives[prim_canon_name] = primitive_canon_token

    expander = Expander(control_sequences,
                        macros, let_chars, parameter_maps, primitives)
    return expander


def get_local_expander():
    control_sequences = {}

    macros = {}
    let_chars = {}
    parameter_maps = {}
    primitives = {}

    expander = Expander(control_sequences,
                        macros, let_chars, parameter_maps, primitives)
    return expander


class Expander(object):

    def __init__(self, control_sequences,
                 macros, let_chars, parameter_maps, primitives):
        self.control_sequences = control_sequences
        self.macros = macros
        self.let_chars = let_chars
        self.parameter_maps = parameter_maps
        self.primitives = primitives

    def expand_macro_to_token_list(self, name, argument_text):
        token = self.get_macro_token(name)
        def_token = token.value['definition']
        def_text_token = def_token.value['text']
        parameter_text = def_text_token.value['parameter_text']
        arguments = parse_argument_text(argument_text, parameter_text)
        replace_text = def_text_token.value['replacement_text']
        finished_text = substitute_params_with_args(replace_text, arguments)
        return finished_text

    def get_routed_control_sequence(self, name):
        route_token = self.control_sequences[name]
        type_ = route_token.type
        if type_ == 'parameter':
            token = self.get_parameter_token(name)
        elif type_ == 'primitive':
            # Give it its primitive type.
            token = self.get_primitive_token(name)
        elif type_ == 'macro':
            token = self.get_macro_token(name)
        elif type_ == 'let_character':
            token = self.get_let_character(name)
        else:
            import pdb; pdb.set_trace()
        return token

    def get_macro_token(self, name):
        # TODO: check what happens if we \let something to a macro,
        # then call \csname on it. Do we get the original macro name?
        route_token = self.control_sequences[name]
        assert route_token.type == 'macro'
        macro_id = route_token.value
        token = self.macros[macro_id]
        assert token.type == 'MACRO'
        return token

    def set_macro(self, name, definition_token, prefixes=None):
        macro_id = len(self.macros)
        route_token = InternalToken(type_='macro', value=macro_id)
        self.control_sequences[name] = route_token

        if prefixes is None:
            prefixes = set()
        macro_token = InternalToken(type_='MACRO',
                                    value={'prefixes': prefixes,
                                           'definition': definition_token})
        self.macros[macro_id] = macro_token
        return macro_token

    def do_short_hand_definition(self, name, def_type, code):
        def_token_type = short_hand_def_to_token_map[def_type]
        primitive_token = TerminalToken(type_=def_token_type, value=code)
        definition_token = make_simple_definition_token(name,
                                                        [primitive_token])
        macro_token = self.set_macro(name, definition_token, prefixes=None)
        return macro_token

    def get_primitive_token(self, name):
        route_token = self.control_sequences[name]
        canonical_name = route_token.value
        canonical_token = self.primitives[canonical_name]
        TokenCls = canonical_token.__class__
        primitive_type = canonical_token.type
        primitive_token = TokenCls(type_=primitive_type, value={'name': name})
        return primitive_token

    def set_let_character(self, name, char_cat_token):
        let_char_id = len(self.let_chars)
        route_token = InternalToken(type_='let_character',
                                    value=let_char_id)
        self.control_sequences[name] = route_token
        self.let_chars[let_char_id] = char_cat_token

    def get_let_character(self, name):
        let_char_id = len(self.let_chars)
        route_token = self.control_sequences[name]
        let_char_id = route_token.value
        token = self.let_chars[let_char_id]
        return token

    def copy_control_sequence(self, existing_name, copy_name):
        # Make a new control sequence that is routed to the same spot as the
        # current one.
        self.control_sequences[copy_name] = self.control_sequences[existing_name]

    def do_let_assignment(self, new_name, target_token):
        if target_token.value['lex_type'] == control_sequence_lex_type:
            target_name = target_token.value['name']
            self.copy_control_sequence(target_name, new_name)
        elif target_token.value['lex_type'] == char_cat_lex_type:
            self.set_let_character(new_name, target_token)
        else:
            import pdb; pdb.set_trace()

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
        return definition_token

    def unpack_param_route(self, name):
        route_token = self.control_sequences[name]
        param_type, param_canon_name = (route_token.value['parameter_type'],
                                        route_token.value['parameter_canonical_name'])
        return param_type, param_canon_name

    def get_parameter_token(self, name):
        param_type, param_canon_name = self.unpack_param_route(name)
        parameter_token = TerminalToken(type_=param_type,
                                        value=param_canon_name)
        return parameter_token

    def get_parameter_value(self, name):
        param_type, param_canon_name = self.unpack_param_route(name)
        parameter_map = self.parameter_maps[param_type]
        parameter_value = parameter_map[param_canon_name]
        return parameter_value

    def set_parameter(self, name, value):
        param_type, param_canon_name = self.unpack_param_route(name)
        parameter_map = self.parameter_maps[param_type]
        parameter_map[param_canon_name] = value

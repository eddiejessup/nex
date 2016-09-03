from common import Token, TerminalToken, InternalToken
from tex_parameters import default_parameters
from typer import (control_sequence_lex_type, char_cat_lex_type,
                   short_hand_def_to_token_map, font_def_token_type,
                   type_primitive_control_sequence,
                   unexpanded_cs_types,
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


class Expander(object):

    def __init__(self, global_state):
        self.global_state = global_state
        self.initialize_control_sequences()

    def initialize_control_sequences(self):
        self.control_sequences = {}
        self.let_map = {}
        self.parameter_maps = default_parameters.copy()

    # TODO: Since we handle internal parameters through this interface,
    # this should probably be renamed.
    def expand_to_token_list(self, name, argument_text):
        if name in self.control_sequences:
            token = self.control_sequences[name]
            if token.type == 'macro':
                def_token = token.value['definition']
                def_text_token = def_token.value['text']
                parameter_text = def_text_token.value['parameter_text']
                arguments = parse_argument_text(argument_text, parameter_text)
                replace_text = def_text_token.value['replacement_text']
                finished_text = substitute_params_with_args(replace_text, arguments)
                return finished_text
            else:
                import pdb; pdb.set_trace()
        else:
            import pdb; pdb.set_trace()

    def expand_to_parameter_text(self, name):
        if name in self.control_sequences:
            token = self.control_sequences[name]
            if token.type == 'macro':
                def_token = token.value['definition']
                def_text_token = def_token.value['text']
                param_text = def_text_token.value['parameter_text']
                return param_text
        else:
            import pdb; pdb.set_trace()

    def name_is_user_control_sequence(self, name):
        return name in self.control_sequences

    def name_is_let_control_sequence(self, name):
        return name in self.let_map

    def get_control_sequence(self, name):
        return self.control_sequences[name]

    def get_let_control_sequence(self, name):
        return self.let_map[name]

    def set_macro(self, name, definition_token, prefixes=None):
        if prefixes is None:
            prefixes = set()
        macro_token = Token(type_='macro',
                            value={'prefixes': prefixes,
                                   'definition': definition_token})
        self.control_sequences[name] = macro_token

    def copy_control_sequence(self, existing_name, copy_name):
        self.control_sequences[copy_name] = self.control_sequences[existing_name][:]

    def resolve_control_sequence(self, token):
        # If it is a macro, leave it alone.
        # If it is a non-macro control sequence.
        if not self.name_is_user_control_sequence(token.value['name']):
            # If it is a let, canonicalize this.
            if self.name_is_let_control_sequence(token.value['name']):
                token = self.get_let_control_sequence(token.value['name'])
            # Note, the following are not 'elif', because we could have a
            # let-ted token that resolves to one of the below cases, and we
            # want to resolve *both* the let and the below case.

            # We might have \let something to a parameter, so we might get an
            # internal thing. This might actually stretch to include many
            # other cases, to the point where this 'iffy' approach is not good.
            if self.is_parameter_token(token):
                pass
            elif token.value['lex_type'] == char_cat_lex_type:
                pass
            # If it is a call to a parameter, resolve this into the
            # underlying parameter token.
            elif self.is_parameter_control_sequence(token.value['name']):
                token = self.get_parameter_token(token.value['name'])
            else:
                # Assume it's a primitive non-parameter control sequence.
                # Give it its primitive type.
                token = type_primitive_control_sequence(token)
        return token

    def do_let_assignment(self, new_name, target_token):
        # TODO: maybe this way of checking for a control sequence is useful
        # in places where we are now checking `type in unexpanded_cs_types`?
        if target_token.value['lex_type'] == control_sequence_lex_type:
            target_token = self.resolve_control_sequence(target_token)
        # Do not merge the above and below seemingly similar checks.
        # The meaning of 'target_token' may change after the above, so
        # we need to check again.
        # If it is a parameter, alias this control sequence to mean that.
        # I think this is different, and better, than aliasing to the
        # parameter *name*, because this might be corrupted by re-defining
        # the parameter control sequence name through \def or whatever.
        if self.is_parameter_token(target_token):
            self.let_map[new_name] = target_token
        # The other cases are lex types.
        elif target_token.value['lex_type'] == control_sequence_lex_type:
            target_name = target_token.value['name']
            # If it is a macro, copy the macro contents into
            # a new macro.
            if self.name_is_user_control_sequence(target_name):
                self.copy_control_sequence(target_name, new_name)
            # Otherwise, it is a primitive control sequence or parameter,
            # and we should just alias this control sequence to mean that.
            else:
                self.let_map[new_name] = target_token
        elif target_token.value['lex_type'] == char_cat_lex_type:
            self.let_map[new_name] = target_token
        else:
            import pdb; pdb.set_trace()

    def define_new_font(self, name, file_name, at_clause):
        new_font_id = self.global_state.global_font_state.define_new_font(file_name,
                                                                          at_clause)
        # Note, this token just records the font id; the information
        # is stored in the global font state (above), because it has internal
        # state that might be modified later; we need to know where to get
        # at it.
        primitive_token = TerminalToken(type_=font_def_token_type,
                                        value=new_font_id)
        definition_token = make_simple_definition_token(name,
                                                        [primitive_token])
        self.set_macro(name, definition_token, prefixes=None)
        return definition_token

    def do_short_hand_definition(self, name, def_type, code):
        def_token_type = short_hand_def_to_token_map[def_type]
        primitive_token = TerminalToken(type_=def_token_type, value=code)
        definition_token = make_simple_definition_token(name,
                                                        [primitive_token])
        self.set_macro(name, definition_token, prefixes=None)
        return definition_token

    def get_parameter_type(self, name):
        for type_, parameter_map in self.parameter_maps.items():
            if name in parameter_map:
                return type_

    def get_parameter_token(self, name):
        type_ = self.get_parameter_type(name)
        parameter_token = TerminalToken(type_=type_, value=name)
        return parameter_token

    def is_parameter_control_sequence(self, name):
        return self.get_parameter_type(name) is not None

    def is_parameter_token(self, token):
        return token.type in self.parameter_maps

    def get_parameter_value(self, name):
        type_ = self.get_parameter_type(name)
        value_map = self.parameter_maps[type_]
        return value_map[name]

    def set_parameter(self, name, value):
        type_ = self.get_parameter_type(name)
        value_map = self.parameter_maps[type_]
        value_map[name] = value

from common import Token, TerminalToken, InternalToken
from tex_parameters import integer_parameters

terminal_primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
    'sfcode': 'SPACE_FACTOR_CODE',
    'delcode': 'DELIMITER_CODE',

    'def': 'DEF',
    'let': 'LET',

    'count': 'COUNT',
    'advance': 'ADVANCE',

    'par': 'PAR',
    'relax': 'RELAX',
    'immediate': 'IMMEDIATE',

    'message': 'MESSAGE',
    'errmessage': 'ERROR_MESSAGE',
    'write': 'WRITE',

    'global': 'GLOBAL',
    'long': 'LONG',
    'outer': 'OUTER',

    'expandafter': 'EXPAND_AFTER',
}


parameter_types = {
    'integer': 'INTEGER_PARAMETER',
}


short_hand_def_map = {
    'chardef': 'CHAR_DEF',
    'mathchardef': 'MATH_CHAR_DEF',
    'countdef': 'COUNT_DEF',
    'dimendef': 'DIMEN_DEF',
    'skipdef': 'SKIP_DEF',
    'muskipdef': 'MU_SKIP_DEF',
    'toksdef': 'TOKS_DEF',
}

short_hand_def_to_token_map = {
    k: '{}_TOKEN'.format(k)
    for k in short_hand_def_map.values()
}

terminal_primitive_control_sequences_map.update(short_hand_def_map)

if_map = {
    'ifnum': 'IF_NUM',
}

non_terminal_primitive_control_sequences_map = {
    'else': 'ELSE',
    'fi': 'END_IF',
    'string': 'STRING',
    'csname': 'CS_NAME',
    'endcsname': 'END_CS_NAME',
}
non_terminal_primitive_control_sequences_map.update(if_map)

primitive_control_sequences_map = dict(**terminal_primitive_control_sequences_map,
                                       **non_terminal_primitive_control_sequences_map)

undelim_macro_param_type = 'UNDELIMITED_PARAM'
delim_macro_param_type = 'DELIMITED_PARAM'
macro_param_types = (undelim_macro_param_type, delim_macro_param_type)

composite_terminal_control_sequence_types = (
    'BALANCED_TEXT_AND_RIGHT_BRACE',
    'PARAMETER_TEXT',
)


def parse_parameter_text(tokens):
    p_nr = 1
    i = 0
    tokens_processed = []
    while i < len(tokens) - 1:
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
    finished_text = replace_text[:]
    for i, t in enumerate(replace_text):
        if t.type == 'PARAM_NUMBER':
            param_nr = t.value
            argument_i = param_nr - 1
            argument = arguments[argument_i]
            finished_text[i] = argument
    return finished_text


def make_simple_macro_token(name, tokens):
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': [],
                                  'replacement_text': tokens})
    def_token = Token(type_='definition',
                      value={'name': name,
                             'text': def_text_token})
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': def_token})
    return macro_token


def make_primitive_macro_token(name, primitive_type, is_terminal):
    value_token = Token(type_=primitive_type, value=name)
    TokenCls = TerminalToken if is_terminal else InternalToken
    primitive_token = TokenCls(type_=primitive_type,
                               value=value_token)
    macro_token = make_simple_macro_token(name, [primitive_token])
    return macro_token


class Expander(object):

    def __init__(self):
        self.initialize_control_sequences()

    def initialize_control_sequences(self):
        self.control_sequences = {}
        self.integer_parameters = {}
        for name, primitive_type in terminal_primitive_control_sequences_map.items():
            self.control_sequences[name] = make_primitive_macro_token(
                name, primitive_type, is_terminal=True)
        for name, primitive_type in non_terminal_primitive_control_sequences_map.items():
            self.control_sequences[name] = make_primitive_macro_token(
                name, primitive_type, is_terminal=False)
        # control_sequences is really a router.
        for int_parameter_name, value in integer_parameters.items():
            parameter_token = TerminalToken(type_=parameter_types['integer'],
                                            value=int_parameter_name)
            self.control_sequences[int_parameter_name] = parameter_token
            self.integer_parameters[int_parameter_name] = value

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
            elif token.type in parameter_types.values():
                return [token]
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
            elif token.type in parameter_types.values():
                return []
        else:
            import pdb; pdb.set_trace()

    def get_control_sequence(self, name):
        return self.control_sequences[name]

    def set_control_sequence(self, name, value):
        self.control_sequences[name] = value

    def do_let_assignment(self, new_name, target_name):
        target_contents = self.get_control_sequence(target_name)
        self.set_control_sequence(new_name, target_contents)

    def do_short_hand_assignment(self, name, def_type, code):
        def_token_type = short_hand_def_to_token_map[def_type]
        primitive_token = TerminalToken(type_=def_token_type, value=code)
        macro_token = make_simple_macro_token(name, [primitive_token])
        self.set_control_sequence(name, macro_token)
        return macro_token

    def get_parameter(self, name):
        return self.integer_parameters[name]

    def set_parameter(self, name, value):
        assert name in integer_parameters.keys()
        self.integer_parameters[name] = value

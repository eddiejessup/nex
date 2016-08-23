from common import Token, TerminalToken


primitive_control_sequences = (
    'relax',
)


primitive_control_sequences_map = {
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
    'write': 'WRITE',

    'global': 'GLOBAL',
    'long': 'LONG',
    'outer': 'OUTER',
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
primitive_control_sequences_map.update(short_hand_def_map)


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


class Expander(object):

    def __init__(self):
        self.initialize_control_sequences()

    def initialize_control_sequences(self):
        self.control_sequences = {}
        for name, primitive_type in primitive_control_sequences_map.items():
            value_token = Token(type_=primitive_type, value=name)
            primitive_token = TerminalToken(type_=primitive_type,
                                            value=value_token)
            def_text_token = Token(type_='definition_text',
                                   value={'parameter_text': [],
                                          'replacement_text': [primitive_token]})
            def_token = Token(type_='definition',
                              value={'name': name,
                                     'text': def_text_token})
            macro_token = Token(type_='macro',
                                value={'prefixes': set(),
                                       'definition': def_token})
            self.control_sequences[name] = macro_token

    def expand_to_token_list(self, name, argument_text):
        # if argument_text: import pdb; pdb.set_trace()
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
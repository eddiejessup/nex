from common import Token, TerminalToken, ascii_characters


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

    'count': 'COUNT',

    'par': 'PAR',
    'relax': 'RELAX',
    'immediate': 'IMMEDIATE',

    'message': 'MESSAGE',
    'write': 'WRITE',
}

prefix_control_sequences = {prefix: 'PREFIX'
                            for prefix in ('global', 'long', 'outer',)}

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
primitive_control_sequences_map.update(prefix_control_sequences)


class Expander(object):

    def __init__(self):
        self.initialize_control_sequences()

    def initialize_control_sequences(self):
        self.control_sequences = {}
        for name, primitive_type in primitive_control_sequences_map.items():
            value_token = Token(type_=primitive_type, value=name)
            primitive_token = TerminalToken(type_=primitive_type,
                                            value=value_token)
            self.control_sequences[name] = [primitive_token]

    def expand_to_token_list(self, name):
        if name in self.control_sequences:
            return self.control_sequences[name]
        else:
            return [TerminalToken(type_=name, value=name)]

    def is_primitive_control_sequence(self, name):
        return True

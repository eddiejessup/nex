from common import TerminalToken, ascii_characters


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

# tokens += tuple(set(primitive_control_sequences_map.values()))
# tokens += tuple(set(short_hand_def_token_map.values()))

# short_hand_def_token_map = {
#     k: '{}_TOKEN'.format(v)
#     for k, v in short_hand_def_map.items()
# }


class Expander(object):

    def __init__(self):
        self.initialize_control_sequences()

    def initialize_control_sequences(self):
        self.control_sequences = {}
        for name, primitive_type in primitive_control_sequences_map.items():
            primitive_token = TerminalToken(type_=primitive_type, value=None)
            self.control_sequences[name] = [primitive_token]
        for c in ascii_characters:
            primitive_token = TerminalToken(type_='SINGLE_CHAR_CONTROL_SEQUENCE', value=None)
            self.control_sequences[name] = [primitive_token]
        # TODO: should these control sequences actually return
        # (char, cat) pairs? Rather than just a plain character?
        # self.control_sequences.update({c: [c] for c in self.char_to_cat})

    def expand_to_token_list(self, name):
        if name in self.control_sequences:
            return self.control_sequences[name]
        else:
            return [TerminalToken(type_=name, value=name)]

    def is_primitive_control_sequence(self, name):
        return True

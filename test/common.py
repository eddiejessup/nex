import os
from enum import Enum

from nex.tokens import InstructionToken, PLYTokenMixin
from nex.parsing import utils as pu

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')

test_chars = list('abc\n')
test_2_chars = list('def\n')


class DummyInstructions(Enum):
    test = 'TEST'


class DummyParameters(Enum):
    ptest = 'TEST_PARAM'


ITok = InstructionToken


# Parsing.

class PTok(PLYTokenMixin):
    def __init__(self, type_, v=None):
        self.type = type_
        self.value = v

    def __repr__(self):
        v = self.value if self.value is not None else ''
        return f'T<{self.type}>({v})'


def str_to_toks(s):
    return [PTok(part) for part in s.split()]


def str_to_lit_strs(s):
    return list(pu.str_to_char_types(s))


def str_to_lit_str(s):
    return ' '.join(str_to_lit_strs(s))

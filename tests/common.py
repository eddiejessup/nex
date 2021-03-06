import os
from enum import Enum

from nex.tokens import InstructionToken, BaseToken
from nex.parsing import utils as pu
from nex.fonts import GlobalFontState
from nex.router import make_char_cat_pair_instruction_token_direct

test_dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(test_dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')
test_runnable_file_name = os.path.join(test_file_dir_path, 'test_runnable.tex')

test_chars = list('abc\n')
test_2_chars = list('def\n')


def char_instr_tok(char, cat):
    return make_char_cat_pair_instruction_token_direct(char, cat, parents=None)


def ITok(*args, **kwargs):
    return InstructionToken(*args, **kwargs, parents=None, value=None)


class DummyInstructions(Enum):
    test = 'TEST'


class DummyCommands(Enum):
    verb = 'VERB'


class DummyParameters(Enum):
    ptest = 'TEST_PARAM'


# Parsing.


def str_to_toks(s):
    return [BaseToken(part) for part in s.split()]


def str_to_lit_strs(s):
    return list(pu.str_to_char_types(s))


def str_to_lit_str(s):
    return ' '.join(str_to_lit_strs(s))


class DummyFontInfo:

    def __init__(self, file_name, file_path, at_clause):
        self.font_name = file_name
        self.file_name = file_name
        self.file_path = file_path
        self.at_clause = at_clause
        self.width = lambda code: 1
        self.height = lambda code: 1
        self.depth = lambda code: 1
        self.x_height = 1


class DummyGlobalFontState(GlobalFontState):

    FontInfo = DummyFontInfo

    def define_new_font(self, file_name, at_clause):
        font_info = DummyFontInfo(file_name=file_name,
                                  file_path=f'/dummy/font/path/{file_name}',
                                  at_clause=at_clause)
        font_id = max(self.fonts.keys()) + 1
        self.fonts[font_id] = font_info
        # Return new font id.
        return font_id

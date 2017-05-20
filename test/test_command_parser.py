from string import ascii_letters

import pytest

from nex.codes import CatCode
from nex.instructions import Instructions
from nex.instructioner import (Instructioner,
                               make_unexpanded_control_sequence_instruction,
                               char_cat_instr_tok)
from nex.utils import ascii_characters
from nex.banisher import Banisher
from nex.parsing.parsing import command_parser


from common import ITok


test_char_to_cat = {}
for c in ascii_characters:
    test_char_to_cat[c] = CatCode.other
for c in ascii_letters:
    test_char_to_cat[c] = CatCode.letter
test_char_to_cat.update({
    '$': CatCode.escape,
    ' ': CatCode.space,
    '[': CatCode.begin_group,
    ']': CatCode.end_group,
    '\n': CatCode.end_of_line,
})


class DummyCodes:
    def __init__(self, char_to_cat):
        if char_to_cat is None:
            self.char_to_cat = test_char_to_cat.copy()
        else:
            self.char_to_cat = char_to_cat

    def get_cat_code(self, char):
        return self.char_to_cat[char]

    def get_lower_case_code(self, c):
        return c.lower()

    def get_upper_case_code(self, c):
        return c.upper()


class DummyRouter:

    def __init__(self, cs_map):
        self.cs_map = cs_map

    def lookup_control_sequence(self, name, *args, **kwargs):
        canon_token = self.cs_map[name]
        return canon_token.copy(*args, **kwargs)


class DummyParameters:

    def __init__(self, param_map):
        self.param_map = param_map

    def get(self, name, *args, **kwargs):
        return self.param_map[name]


class DummyState:

    def __init__(self, char_to_cat, cs_map, param_map=None):
        self.router = DummyRouter(cs_map)
        self.parameters = DummyParameters(param_map)
        self.codes = DummyCodes(char_to_cat)


def string_to_banisher(s, cs_map, char_to_cat=None, param_map=None):
    state = DummyState(cs_map=cs_map,
                       param_map=param_map, char_to_cat=char_to_cat)
    instrs = Instructioner.from_string(s, get_cat_code_func=state.codes.get_cat_code)
    return Banisher(instrs, state, instrs.lexer.reader)


def test_h_rule():
    cs_map = {
        'hRule': ITok(Instructions.h_rule),
    }
    b = string_to_banisher('$hRule height 20pt width 10pt depth 30pt', cs_map)
    command_parser.parse(b.advance_to_end())


def test_accent():
    cs_map = {
        'alloAllo': ITok(Instructions.accent),
    }
    b = string_to_banisher('$alloAllo22', cs_map)
    command_parser.parse(b.advance_to_end())


def test_un_h_box():
    cs_map = {
        'unwrapHBox': ITok(Instructions.un_h_box),
    }
    b = string_to_banisher('$unwrapHBox 12', cs_map)
    command_parser.parse(b.advance_to_end())

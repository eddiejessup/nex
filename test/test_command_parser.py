from string import ascii_letters

import pytest

from nex.constants.codes import CatCode
from nex.constants.instructions import Instructions, unexpanded_cs_instructions
from nex.instructioner import (Instructioner,
                               make_unexpanded_control_sequence_instruction,
                               char_cat_instr_tok)
from nex.utils import ascii_characters
from nex.parsing import parsing

from common import ITok

parser = parsing.get_parser(start='command', chunking=False)


char_to_cat = {}
for c in ascii_characters:
    char_to_cat[c] = CatCode.other
for c in ascii_letters:
    char_to_cat[c] = CatCode.letter
char_to_cat.update({
    '$': CatCode.escape,
    ' ': CatCode.space,
    '[': CatCode.begin_group,
    ']': CatCode.end_group,
    '\n': CatCode.end_of_line,
})


cs_map = {
    'hRule': ITok(Instructions.h_rule),
    'alloAllo': ITok(Instructions.accent),
    'unwrapHBox': ITok(Instructions.un_h_box),
    'HBox': ITok(Instructions.h_box),
    'HMaterial': ITok(Instructions.horizontal_mode_material_and_right_brace),
    'assignThen': ITok(Instructions.after_assignment),
    'groupThen': ITok(Instructions.after_group),
}


def process(s):
    """
    Just resolves control sequences, enough to allow convenient string input
    in tests.
    """
    instrs = Instructioner.from_string(
        s, get_cat_code_func=char_to_cat.get)
    while True:
        try:
            t = next(instrs)
        except EOFError:
            return
        else:
            if t.instruction in unexpanded_cs_instructions:
                t = cs_map[t.value['name']]
            yield t


def test_h_rule():
    parser.parse(process('$hRule height 20pt width 10pt depth 30pt'))


def test_accent():
    parser.parse(process('$alloAllo22'))


def test_set_box():
    parser.parse(process('$unwrapHBox 12'))


def test_un_h_box():
    parser.parse(process('$unwrapHBox 12'))


def test_box_literal():
    parser.parse(process('$HBox to 2pt [$HMaterial'))


def test_after_assignment():
    ts = [ITok(Instructions.after_assignment),
          ITok(Instructions.arbitrary_token)]
    parser.parse(iter(ts))


def test_after_group():
    ts = [ITok(Instructions.after_group),
          ITok(Instructions.arbitrary_token)]
    parser.parse(iter(ts))

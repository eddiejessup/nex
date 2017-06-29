from string import ascii_letters

import pytest

from nex.constants.codes import CatCode
from nex.constants.instructions import Instructions, unexpanded_cs_instructions
from nex.router import (Instructioner,
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
    '`': CatCode.math_shift,
})


cs_map = {
    'noOp': ITok(Instructions.relax),
    'hRule': ITok(Instructions.h_rule),
    'vRule': ITok(Instructions.v_rule),
    'addAccent': ITok(Instructions.accent),
    'unwrapHBox': ITok(Instructions.un_h_box),
    'unloadHBox': ITok(Instructions.un_h_copy),
    'unwrapVBox': ITok(Instructions.un_v_box),
    'unloadVBox': ITok(Instructions.un_v_copy),
    'HBox': ITok(Instructions.h_box),
    'VBox': ITok(Instructions.v_box),
    'HMaterial': ITok(Instructions.horizontal_mode_material_and_right_brace),
    'VMaterial': ITok(Instructions.vertical_mode_material_and_right_brace),
    'assignThen': ITok(Instructions.after_assignment),
    'groupThen': ITok(Instructions.after_group),
    'rightLiteralBrace': ITok(Instructions.right_brace),
    'startGroup': ITok(Instructions.begin_group),
    'finishGroup': ITok(Instructions.end_group),
    'displayLists': ITok(Instructions.show_lists),
    'openInput': ITok(Instructions.open_input),
    'openOutput': ITok(Instructions.open_output),
    'closeInput': ITok(Instructions.close_input),
    'closeOutput': ITok(Instructions.close_output),
    'print': ITok(Instructions.write),
    'tell': ITok(Instructions.message),
    'errTell': ITok(Instructions.error_message),
    'someText': ITok(Instructions.balanced_text_and_right_brace),
    'someToken': ITok(Instructions.arbitrary_token),
    'sendOut': ITok(Instructions.ship_out),
    'kern': ITok(Instructions.kern),
    'mKern': ITok(Instructions.math_kern),
    'undoPenalty': ITok(Instructions.un_penalty),
    'undoKern': ITok(Instructions.un_kern),
    'undoGlue': ITok(Instructions.un_glue),
    'hGlue': ITok(Instructions.h_skip),
    'vGlue': ITok(Instructions.v_skip),
    'normalSpace': ITok(Instructions.space),
    'controlSpace': ITok(Instructions.control_space),
    'doIndent': ITok(Instructions.indent),
    'doNotIndent': ITok(Instructions.no_indent),
    'doPara': ITok(Instructions.par),
    'finish': ITok(Instructions.end),
    'dumpOut': ITok(Instructions.dump),
    'italCorrect': ITok(Instructions.italic_correction),
    'maybeHyphen': ITok(Instructions.discretionary_hyphen),
    'ignoreSpaces': ITok(Instructions.ignore_spaces),
    'doSpecial': ITok(Instructions.special),
    'addPenalty': ITok(Instructions.add_penalty),
    'addMark': ITok(Instructions.mark),
    'addInsertion': ITok(Instructions.insert),
    'vAdjust': ITok(Instructions.v_adjust),
    'normalLeaders': ITok(Instructions.leaders),
    'centeredLeaders': ITok(Instructions.centered_leaders),
    'expandedLeaders': ITok(Instructions.expanded_leaders),
}


def process(s):
    """
    Just resolves control sequences, enough to allow convenient string input
    in tests.
    """
    def resolve_cs(name, *args, **kwargs):
        return cs_map[name]
    instrs = Instructioner.from_string(
        s=s,
        resolve_cs_func=resolve_cs,
        get_cat_code_func=char_to_cat.get,
    )
    return instrs.advance_to_end(expand=True)


def test_relax():
    parser.parse(process('$noOp'))


def test_right_brace():
    parser.parse(process('$rightLiteralBrace'))


def test_delimit_group():
    parser.parse(process('$startGroup'))
    parser.parse(process('$finishGroup'))


def test_show_lists():
    parser.parse(process('$displayLists'))


def test_ship_out():
    parser.parse(process('$sendOut $HBox[$HMaterial'))


def test_after_assignment():
    parser.parse(process('$assignThen $someToken'))


def test_after_group():
    parser.parse(process('$groupThen $someToken'))


def test_message():
    parser.parse(process('$tell [$someText'))
    parser.parse(process('$errTell [$someText'))


def test_open_io():
    parser.parse(process('$openInput 1 =inFile'))
    parser.parse(process('$openOutput 2 =outFile'))


def test_close_io():
    parser.parse(process('$closeInput 1'))
    parser.parse(process('$closeOutput 2'))


def test_write():
    parser.parse(process('$print 1 [$someText'))


def test_special():
    parser.parse(process('$doSpecial [$someText'))


def test_penalty():
    parser.parse(process('$addPenalty 1000'))


def test_kern():
    parser.parse(process('$kern 30sp'))
    parser.parse(process('$mKern 30mu'))


def test_mark():
    parser.parse(process('$addMark [$someText'))


def test_insert():
    parser.parse(process('$addInsertion 28   [$VMaterial'))


def test_v_adjust():
    parser.parse(process('$vAdjust  [$VMaterial'))


def test_un_stuff():
    parser.parse(process('$undoPenalty'))
    parser.parse(process('$undoKern'))
    parser.parse(process('$undoGlue'))


def test_glue():
    parser.parse(process('$hGlue 10em'))
    parser.parse(process('$vGlue 10cc'))


def test_space():
    parser.parse(process('$normalSpace'))
    parser.parse(process('$controlSpace'))


def test_add_leaders():
    parser.parse(process('$normalLeaders $hRule height 20pt $hGlue 10em'))
    parser.parse(process('$centeredLeaders $vRule width 20pt $vGlue 1.3cc'))
    parser.parse(process('$expandedLeaders $hRule depth 20pt $hGlue 1.3cc'))


def test_box_literal():
    parser.parse(process('$HBox to 2pt[$HMaterial'))
    parser.parse(process('$VBox spread 5in [$VMaterial'))


def test_un_box():
    parser.parse(process('$unwrapHBox 12'))
    parser.parse(process('$unloadHBox 12'))
    parser.parse(process('$unwrapVBox 12'))
    parser.parse(process('$unloadVBox 12'))


def test_indent():
    parser.parse(process('$doIndent'))
    parser.parse(process('$doNotIndent'))


def test_par():
    parser.parse(process('$doPara'))


def test_left_brace():
    parser.parse(process('['))


def test_rule():
    parser.parse(process('$hRule height 20pt width 10pt depth 30pt'))
    parser.parse(process('$vRule height 20em width 10cc depth 2.5in'))


def test_endings():
    parser.parse(process('$finish'))
    parser.parse(process('$dumpOut'))


def test_character():
    parser.parse(process('a'))


def test_accent():
    parser.parse(process('$addAccent22'))
    parser.parse(process('$addAccent22 c'))


def test_italic_correction():
    parser.parse(process('$italCorrect'))


def test_discretionary():
    parser.parse(process('$maybeHyphen'))


def test_math_shift():
    parser.parse(process('`'))


def test_ignore_spaces():
    parser.parse(process('$ignoreSpaces       '))

import pytest

from string import ascii_letters
from enum import Enum

from nex.codes import CatCode
from nex.banisher import Banisher, BanisherError
from nex.tokens import InstructionToken
from nex.tex_parameters import Parameters
from nex.instructions import Instructions
from nex.instructioner import (Instructioner,
                               make_unexpanded_control_sequence_instruction,
                               make_instruction_token_from_char_cat)
from nex.router import make_macro_token
from nex.utils import ascii_characters


class DummyInstructions(Enum):
    test = 'TEST'


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
})


def string_to_banisher(s, cs_map, char_to_cat=None, param_map=None):
    state = DummyState(cs_map=cs_map,
                       param_map=param_map, char_to_cat=char_to_cat)
    instrs = Instructioner.from_string(s, get_cat_code_func=state.get_cat_code)
    return Banisher(instrs, state, instrs.lexer.reader)


class DummyState:

    def __init__(self, char_to_cat, cs_map, param_map=None):
        if char_to_cat is None:
            self.char_to_cat = test_char_to_cat.copy()
        else:
            self.char_to_cat = char_to_cat
        self.cs_map = cs_map
        self.param_map = param_map

    def resolve_control_sequence_to_token(self, name, *args, **kwargs):
        canon_token = self.cs_map[name]
        token = canon_token.copy(*args, **kwargs)
        return token

    def get_parameter_value(self, parameter):
        return self.param_map[parameter]

    def get_cat_code(self, char):
        return self.char_to_cat[char]

    def get_lower_case_code(self, c):
        return c.lower()

    def get_upper_case_code(self, c):
        return c.upper()


def test_resolver():
    cs_map = {
        'hi': InstructionToken(DummyInstructions.test),
    }
    b = string_to_banisher('$hi', cs_map)
    out = b.get_next_output_list()
    assert len(out) == 1 and out[0] == cs_map['hi']


def test_empty_macro():
    cs_map = {
        'macro': make_macro_token(name='macro',
                                  replacement_text=[], parameter_text=[]),
    }
    b = string_to_banisher('$macro', cs_map)
    out = b._iterate()
    assert out is None
    assert list(b.instructions.advance_to_end()) == []


def test_short_hand_def():
    cs_map = {
        'cd': InstructionToken(Instructions.count_def),
    }
    b = string_to_banisher('$cd $myBestNumber', cs_map)
    out = b.get_next_output_list()
    assert len(out) == 2
    assert out[0] == cs_map['cd']
    assert out[1].value['name'] == 'myBestNumber'


def test_def():
    cs_map = {
        'df': InstructionToken(Instructions.def_),
    }
    b = string_to_banisher('$df $myName[$sayLola]', cs_map)
    out = b._iterate()
    assert len(out) == 5


def test_let():
    cs_map = {
        'letrill': InstructionToken(Instructions.let),
    }
    b_minimal = string_to_banisher('$letrill $cheese a', cs_map)
    out_minimal = b_minimal._iterate()
    assert len(out_minimal) == 3

    b_equals = string_to_banisher('$letrill $cheese=a', cs_map)
    out_equals = b_equals._iterate()
    assert len(out_equals) == 4

    b_maximal = string_to_banisher('$letrill $cheese= a', cs_map)
    out_maximal = b_maximal._iterate()
    # print(out_maximal)
    assert len(out_maximal) == 5

    assert out_minimal[-1] == out_equals[-1] == out_maximal[-1]


def test_toks_def_balanced():
    cs_map = {
        'bestToks': InstructionToken(Instructions.token_parameter),
    }
    b = string_to_banisher('$bestToks [[$this] and $that]', cs_map)
    out = b._iterate()
    # First time, just get first token and set context to wait for balanced
    # text.
    assert len(out) == 1
    # Second time, grab balanced text.
    out = b._iterate()
    assert len(out) == 2
    assert out[-1].instruction == Instructions.balanced_text_and_right_brace
    assert len(out[-1].value) == 9


def test_toks_assign_literal():
    cs_map = {
        'bestToks': InstructionToken(Instructions.token_parameter),
    }
    b = string_to_banisher('$bestToks [[$this] and $that]', cs_map)
    out = b._iterate()
    # First time, just get first token and set context to wait for balanced
    # text.
    assert len(out) == 1
    # Second time, grab balanced text.
    out = b._iterate()
    assert len(out) == 2
    assert out[-1].instruction == Instructions.balanced_text_and_right_brace
    assert len(out[-1].value) == 9


def test_toks_assign_variable():
    cs_map = {
        'bestOfToks': InstructionToken(Instructions.token_parameter),
        'worstOfToks': InstructionToken(Instructions.token_parameter),
    }
    b = string_to_banisher('$bestOfToks $worstOfToks', cs_map)
    out = b._iterate()
    # First time, just get first token and set context to wait for balanced
    # text.
    assert len(out) == 1
    # Second time, grab target toks.
    out = b._iterate()
    assert len(out) == 1
    assert out[-1].instruction == Instructions.token_parameter


def test_expand_after():
    def_target = make_unexpanded_control_sequence_instruction('defTarget')
    cs_map = {
        'expandAfter': InstructionToken(Instructions.expand_after),
        'defCount': InstructionToken(Instructions.count_def),
        'getTarget': make_macro_token(name='getTarget',
                                      replacement_text=[def_target],
                                      parameter_text=[]),
    }
    # Should expand $getTarget to [$defTarget], then expand $defCount, which
    # should then read $defTarget as its argument.
    b = string_to_banisher('$expandAfter $defCount $getTarget', cs_map)
    out = b.get_next_output_list()
    assert len(out) == 2
    assert out[0] == cs_map['defCount']
    assert out[1] == def_target


def test_string_control_sequence():
    cs_map = {
        'getString': InstructionToken(Instructions.string),
    }
    param_map = {
        Parameters.escape_char: ord('@'),
    }
    b = string_to_banisher('$getString $CS', cs_map, param_map=param_map)
    out = b.get_next_output_list()
    assert all(t.value['cat'] == CatCode.other for t in out)
    assert ''.join(t.value['char'] for t in out) == '@CS'


def test_string_character():
    cs_map = {
        'getString': InstructionToken(Instructions.string),
    }
    param_map = {
        Parameters.escape_char: ord('@'),
    }
    b = string_to_banisher('$getString A', cs_map, param_map=param_map)
    out = b.get_next_output_list()
    assert all(t.value['cat'] == CatCode.other for t in out)
    assert ''.join(t.value['char'] for t in out) == 'A'


def test_string_control_sequence_containing_space():
    cs_map = {
        'getString': InstructionToken(Instructions.string),
    }
    param_map = {
        Parameters.escape_char: ord('@'),
    }
    char_to_cat_weird = test_char_to_cat.copy()
    char_to_cat_weird[' '] = CatCode.letter

    b = string_to_banisher('$getString$CS WITH SPACES', cs_map,
                           char_to_cat=char_to_cat_weird,
                           param_map=param_map)
    out = b.get_next_output_list()
    for t in out:
        if t.value['char'] == ' ':
            correct_cat = CatCode.space
        else:
            correct_cat = CatCode.other
        assert t.value['cat'] == correct_cat
    assert ''.join(t.value['char'] for t in out) == '@CS WITH SPACES'


def test_string_control_sequence_no_escape():
    cs_map = {
        'getString': InstructionToken(Instructions.string),
    }
    param_map = {
        # Negative value should cause no escape character to be shown.
        Parameters.escape_char: -1,
    }

    b = string_to_banisher('$getString$NoEscapeCS', cs_map,
                           param_map=param_map)
    out = b.get_next_output_list()
    assert all(t.value['cat'] == CatCode.other for t in out)
    assert ''.join(t.value['char'] for t in out) == 'NoEscapeCS'


def test_cs_name():
    char = 'a'
    a_token = make_instruction_token_from_char_cat(char, CatCode.letter)
    make_A_token = make_macro_token(name='theA',
                                    replacement_text=[a_token],
                                    parameter_text=[])
    cs_map = {
        'getCSName': InstructionToken(Instructions.cs_name),
        'endCSName': InstructionToken(Instructions.end_cs_name),
        'theA': make_A_token,
    }

    b = string_to_banisher('$getCSName theA$endCSName', cs_map)
    # In the first iteration, should make a $theA control sequence call.
    # In the second iteration, should expand $theA to `a_token`.
    out = b.get_next_output_list()
    assert len(out) == 1
    assert out[0] == a_token


def test_cs_name_end_by_expansion():
    # I seem to have made this test very complicated. The idea is that a macro,
    # $theFThenEnd, makes the string 'theF' then '\endcsname'.
    # This is then procesed by \csname, to produce a control sequence call
    # '$theF'.
    # This control sequence is then expanded to the string 'F'.
    char = 'F'
    F_token = make_instruction_token_from_char_cat(char, CatCode.letter)
    cs_name = 'theF'
    get_lett_instr = lambda c: make_instruction_token_from_char_cat(c, CatCode.letter)
    the_F_then_end_token = make_macro_token(
        name='theFThenEnd',
        replacement_text=[get_lett_instr(c) for c in cs_name] + [InstructionToken(Instructions.end_cs_name)],
        parameter_text=[]
    )
    make_F_token = make_macro_token(name='theF',
                                    replacement_text=[F_token],
                                    parameter_text=[])
    cs_map = {
        'getCSName': InstructionToken(Instructions.cs_name),
        'theFThenEnd': the_F_then_end_token,
        'theF': make_F_token,
    }

    b = string_to_banisher('$getCSName $theFThenEnd', cs_map)
    # In the first iteration, should make a $AND control sequence call.
    # In the second iteration, should expand $AND to `a_token`.
    out = b.get_next_output_list()
    assert len(out) == 1
    assert out[0] == F_token


def test_cs_name_containing_non_char():
    cs_map = {
        'getCSName': InstructionToken(Instructions.cs_name),
        'endCSName': InstructionToken(Instructions.end_cs_name),
        'primitive': InstructionToken(DummyInstructions.test),
    }

    b = string_to_banisher('$getCSName $primitive $endCSName', cs_map)
    with pytest.raises(BanisherError):
        b.get_next_output_list()


def test_change_case():
    B_token = make_instruction_token_from_char_cat('B', CatCode.letter)
    make_B_token = make_macro_token(name='makeB', replacement_text=[B_token],
                                    parameter_text=[])
    y_token = make_instruction_token_from_char_cat('y', CatCode.letter)
    make_y_token = make_macro_token(name='makey', replacement_text=[y_token],
                                    parameter_text=[])

    cs_map = {
        'upper': InstructionToken(Instructions.upper_case),
        'lower': InstructionToken(Instructions.lower_case),
        'makeB': make_B_token,
        'makey': make_y_token,
    }

    b = string_to_banisher('$upper[abc]', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'ABC'

    b = string_to_banisher('$lower[XYZ]', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'xyz'

    b = string_to_banisher('$lower[A$makeB C]', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'aBc'

    b = string_to_banisher('$upper[x$makey z]', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'XyZ'

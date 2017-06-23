from string import ascii_letters

import pytest

from nex.constants.codes import CatCode
from nex.constants.parameters import Parameters
from nex.constants.instructions import Instructions
from nex.banisher import Banisher
from nex.router import (Instructioner,
                        make_unexpanded_control_sequence_instruction,
                        make_macro_token,
                        char_cat_instr_tok)
from nex.utils import ascii_characters, UserError

from common import DummyInstructions, ITok


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

    def name_means_start_condition(self, name):
        return name in ('ifYes', 'ifNo')

    def name_means_end_condition(self, name):
        return name == 'endIf'

    def name_means_delimit_condition(self, name):
        return name in ('else', 'ooor')


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

    def evaluate_if_token_to_block(self, tok):
        if tok.type == Instructions.if_true.value:
            return 0
        elif tok.type == Instructions.if_false.value:
            return 1
        else:
            raise Exception


def string_to_banisher(s, cs_map, char_to_cat=None, param_map=None):
    state = DummyState(cs_map=cs_map,
                       param_map=param_map, char_to_cat=char_to_cat)
    instructions = Instructioner.from_string(
        resolve_cs_func=state.router.lookup_control_sequence,
        s=s,
        get_cat_code_func=state.codes.get_cat_code
    )
    return Banisher(instructions, state, instructions.lexer.reader)


def test_resolver():
    cs_map = {
        'hi': ITok(DummyInstructions.test),
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
        'cd': ITok(Instructions.count_def),
    }
    b = string_to_banisher('$cd $myBestNumber', cs_map)
    out = b.get_next_output_list()
    assert len(out) == 2
    assert out[0] == cs_map['cd']
    assert out[1].value['name'] == 'myBestNumber'


def test_def():
    cs_map = {
        'df': ITok(Instructions.def_),
    }
    b = string_to_banisher('$df $myName[$sayLola]', cs_map)
    out = b._iterate()
    assert len(out) == 5


def test_let():
    cs_map = {
        'letrill': ITok(Instructions.let),
    }
    b_minimal = string_to_banisher('$letrill $cheese a', cs_map)
    out_minimal = b_minimal._iterate()
    assert len(out_minimal) == 3

    b_equals = string_to_banisher('$letrill $cheese=a', cs_map)
    out_equals = b_equals._iterate()
    assert len(out_equals) == 4

    b_maximal = string_to_banisher('$letrill $cheese= a', cs_map)
    out_maximal = b_maximal._iterate()
    assert len(out_maximal) == 5

    assert out_minimal[-1] == out_equals[-1] == out_maximal[-1]


def test_toks_def_balanced():
    cs_map = {
        'bestToks': ITok(Instructions.token_parameter),
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
        'bestToks': ITok(Instructions.token_parameter),
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
        'bestOfToks': ITok(Instructions.token_parameter),
        'worstOfToks': ITok(Instructions.token_parameter),
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
        'expandAfter': ITok(Instructions.expand_after),
        'defCount': ITok(Instructions.count_def),
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
        'getString': ITok(Instructions.string),
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
        'getString': ITok(Instructions.string),
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
        'getString': ITok(Instructions.string),
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
        'getString': ITok(Instructions.string),
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
    a_token = char_cat_instr_tok(char, CatCode.letter)
    make_A_token = make_macro_token(name='theA',
                                    replacement_text=[a_token],
                                    parameter_text=[])
    cs_map = {
        'getCSName': ITok(Instructions.cs_name),
        'endCSName': ITok(Instructions.end_cs_name),
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
    F_token = char_cat_instr_tok(char, CatCode.letter)
    cs_name = 'theF'
    the_F_then_end_token = make_macro_token(
        name='theFThenEnd',
        replacement_text=([char_cat_instr_tok(c, CatCode.letter)
                           for c in cs_name] +
                          [ITok(Instructions.end_cs_name)]),
        parameter_text=[]
    )
    make_F_token = make_macro_token(name='theF',
                                    replacement_text=[F_token],
                                    parameter_text=[])
    cs_map = {
        'getCSName': ITok(Instructions.cs_name),
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
        'getCSName': ITok(Instructions.cs_name),
        'endCSName': ITok(Instructions.end_cs_name),
        'primitive': ITok(DummyInstructions.test),
    }

    b = string_to_banisher('$getCSName $primitive $endCSName', cs_map)
    with pytest.raises(UserError):
        b.get_next_output_list()


def test_change_case():
    B_token = char_cat_instr_tok('B', CatCode.letter)
    make_B_token = make_macro_token(name='makeB', replacement_text=[B_token],
                                    parameter_text=[])
    y_token = char_cat_instr_tok('y', CatCode.letter)
    make_y_token = make_macro_token(name='makey', replacement_text=[y_token],
                                    parameter_text=[])

    cs_map = {
        'upper': ITok(Instructions.upper_case),
        'lower': ITok(Instructions.lower_case),
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


def test_if():
    cs_map = {
        'ifYes': ITok(Instructions.if_true),
        'ifNo': ITok(Instructions.if_false),
        'else': ITok(Instructions.else_),
        'endIf': ITok(Instructions.end_if),
    }

    b = string_to_banisher('$ifYes abc$else def $endIf', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'abc'

    b = string_to_banisher('$ifNo abc$else def$endIf', cs_map)
    out = b.advance_to_end()
    assert ''.join(t.value['char'] for t in out) == 'def'


def test_afters():
    cs_map = {
        'assignThen': ITok(Instructions.after_assignment),
        'groupThen': ITok(Instructions.after_group),
    }
    for cs in cs_map:
        b = string_to_banisher(f'${cs} $something', cs_map)
        out = b.get_next_output_list()
        assert len(out) == 2
        assert out[0] == cs_map[cs]
        assert out[1].instruction == Instructions.arbitrary_token
        target_tok = out[1].value
        assert target_tok.value['name'] == 'something'

from string import ascii_letters
from enum import Enum

from nex.codes import CatCode
from nex.banisher import Banisher
from nex.tokens import InstructionToken
from nex.instructions import Instructions
from nex.instructioner import Instructioner, make_control_sequence_instruction_token
from nex.router import make_macro_token
from nex.utils import ascii_characters


class DummyInstructions(Enum):
    test = 'TEST'


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
})


class DummyCatCodeGetter:

    def __init__(self):
        # self.char_to_cat = get_initial_char_cats()
        self.char_to_cat = char_to_cat.copy()

    def get(self, char):
        return self.char_to_cat[char]


def string_to_instructions(s):
    cat_code_getter = DummyCatCodeGetter()
    return Instructioner.from_string(s, get_cat_code_func=cat_code_getter.get)


def string_to_banisher(s, cs_map):
    st = DummyState()
    instrs = string_to_instructions(s)

    def resolve_control_sequence(name, *args, **kwargs):
        canon_token = cs_map[name]
        token = canon_token.copy(*args, **kwargs)
        # Amend canonical tokens to give them the proper control sequence
        # 'name'.
        if isinstance(token.value, dict) and 'name' in token.value:
            token.value['name'] = name
        return token

    return Banisher(instrs, st, instrs.lexer.reader,
                    resolve_control_sequence_func=resolve_control_sequence)


class DummyState:
    pass


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
    def_target = make_control_sequence_instruction_token('defTarget')
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

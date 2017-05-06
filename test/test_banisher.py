from string import ascii_letters
from enum import Enum

from nex.codes import get_initial_char_cats, CatCode
from nex.banisher import Banisher
from nex.tokens import InstructionToken
from nex.instructions import Instructions
from nex.instructioner import Instructioner
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


cs_instr_map = {
    'hi': InstructionToken(DummyInstructions.test),
    'macro': make_macro_token(name='macro',
                              replacement_text=[], parameter_text=[]),
    'cd': InstructionToken(Instructions.count_def),
    'df': InstructionToken(Instructions.def_),
}


def resolve_control_sequence(name, *args, **kwargs):
    canon_token = cs_instr_map[name]
    token = canon_token.copy(*args, **kwargs)
    # Amend canonical tokens to give them the proper control sequence
    # 'name'.
    if isinstance(token.value, dict) and 'name' in token.value:
        token.value['name'] = name
    return token


class DummyState:
    pass


def test_resolver():
    st = DummyState()
    instrs = string_to_instructions('$hi')
    b = Banisher(instrs, st, instrs.lexer.reader,
                 resolve_control_sequence_func=resolve_control_sequence)
    out = b.get_next_output_list()
    assert len(out) == 1 and out[0] == cs_instr_map['hi']


def test_empty_macro():
    st = DummyState()
    instrs = string_to_instructions('$macro')
    b = Banisher(instrs, st, instrs.lexer.reader,
                 resolve_control_sequence_func=resolve_control_sequence)
    out = b._iterate()
    assert out is None
    assert list(instrs.advance_to_end()) == []


def test_short_hand_def():
    st = DummyState()
    instrs = string_to_instructions('$cd $myBestNumber')
    b = Banisher(instrs, st, instrs.lexer.reader,
                 resolve_control_sequence_func=resolve_control_sequence)
    out = b.get_next_output_list()
    assert len(out) == 2
    assert out[0] == cs_instr_map['cd']
    assert out[1].value['name'] == 'myBestNumber'


def test_def():
    st = DummyState()
    instrs = string_to_instructions('$df $myName[$sayLola]')
    b = Banisher(instrs, st, instrs.lexer.reader,
                 resolve_control_sequence_func=resolve_control_sequence)
    out = b._iterate()
    assert len(out) == 5
    for t in out:
        print(t)
        # print(t.get_position_str(b.reader))

import pytest

from nex.codes import CatCode
from nex.router import CSRouter
from nex.utils import NoSuchControlSequence
from nex.instructioner import (make_unexpanded_control_sequence_instruction,
                               char_cat_instr_tok)
from nex.instructions import Instructions

from common import DummyInstructions, DummyParameters, ITok

dummy_token = make_unexpanded_control_sequence_instruction('dummy')


def test_undefined_control_sequence():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    with pytest.raises(NoSuchControlSequence):
        r.lookup_control_sequence(name='test')
    with pytest.raises(NoSuchControlSequence):
        r.do_let_assignment(target_token=dummy_token, new_name='test_2')


def test_primitive_resolution():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={'hi': DummyInstructions.test},
                 enclosing_scope=None)
    t = r.lookup_control_sequence('hi')
    assert t.value['name'] == 'hi'
    assert t.instruction == DummyInstructions.test


def test_parameter_resolution():
    pcs = {'ho': (DummyParameters.ptest, DummyInstructions.test)}
    r = CSRouter(param_control_sequences=pcs,
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    t = r.lookup_control_sequence('ho')
    assert t.value['name'] == 'ho'
    assert t.value['parameter'] == DummyParameters.ptest
    assert t.instruction == DummyInstructions.test


def test_macro_definition():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    repl = [ITok(DummyInstructions.test)]
    r.set_macro(name='hi', replacement_text=repl, parameter_text=[],
                def_type=None, prefixes=None)
    t = r.lookup_control_sequence('hi')
    assert t.value['name'] == 'hi'
    assert t.value['replacement_text'] == repl
    assert len(t.value['prefixes']) == 0
    assert isinstance(t.value['prefixes'], set)


def test_short_hand_macro_definition():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    code = 200
    r.do_short_hand_definition('hi', def_type=Instructions.char_def.value,
                               code=code)
    t = r.lookup_control_sequence('hi')
    assert t.value['name'] == 'hi'
    assert t.value['def_type'] == 'sdef'
    assert len(t.value['replacement_text']) == 1
    tok = t.value['replacement_text'][0]
    assert tok.value == code
    assert tok.instruction == Instructions.char_def_token


def test_let_to_macro():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    code = 200
    r.do_short_hand_definition('hi', def_type=Instructions.char_def.value,
                               code=code)
    t = r.lookup_control_sequence('hi')
    r.do_let_assignment('new_way_to_say_hi', t)
    t_let = r.lookup_control_sequence('new_way_to_say_hi')

    assert t.value['name'] == 'hi'
    assert t_let.value['name'] == 'new_way_to_say_hi'
    assert t_let.instruction == t.instruction
    assert t_let.value['replacement_text'] is t.value['replacement_text']

    # Check letting to a let token.
    r.do_let_assignment('even_newer_way_to_say_hi', t_let)
    t_even_newer = r.lookup_control_sequence('even_newer_way_to_say_hi')
    assert t_even_newer.value['name'] == 'even_newer_way_to_say_hi'
    assert t_even_newer.instruction == t.instruction
    assert t_even_newer.value['replacement_text'] is t.value['replacement_text']


def test_let_to_primitive():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={'hi': DummyInstructions.test},
                 enclosing_scope=None)
    t = r.lookup_control_sequence('hi')
    r.do_let_assignment('new_way_to_say_hi', t)
    t_let = r.lookup_control_sequence('new_way_to_say_hi')
    assert t.value['name'] == 'hi'
    assert t_let.value['name'] == 'new_way_to_say_hi'
    assert t_let.instruction == t.instruction


def test_let_to_parameter():
    pcs = {'ho': (DummyParameters.ptest, DummyInstructions.test)}
    r = CSRouter(param_control_sequences=pcs,
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    t = r.lookup_control_sequence('ho')
    r.do_let_assignment('new_way_to_say_ho', t)
    t_let = r.lookup_control_sequence('new_way_to_say_ho')
    assert t.value['name'] == 'ho'
    assert t_let.value['name'] == 'new_way_to_say_ho'
    assert t_let.instruction == t.instruction
    assert t_let.value['parameter'] == t.value['parameter']


def test_let_to_character():
    r = CSRouter(param_control_sequences={},
                 special_control_sequences={},
                 primitive_control_sequences={},
                 enclosing_scope=None)
    targ = char_cat_instr_tok('c', CatCode.letter)
    r.do_let_assignment('c', targ)
    t_let = r.lookup_control_sequence('c')
